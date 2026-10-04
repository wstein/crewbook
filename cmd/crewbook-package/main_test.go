package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/wstein/crewbook/internal/packagefmt"
)

func sourceFixture(t *testing.T) string {
	t.Helper()
	root, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if err = os.Mkdir(filepath.Join(root, "tools"), 0755); err != nil {
		t.Fatal(err)
	}
	layout := `{"schema_version":1,"name":"crewbook","license":"EUPL-1.2","entrypoints":{"skill":"SKILL.md","roles":[],"claude_agents":[],"claude_commands":[]},"resources":["crewbook.json","LICENSE"],"host_dependencies":[]}`
	policy := packagefmt.Policy{Version: 1, Distributed: []string{"LICENSE", "SKILL.md", "crewbook.json"}, Maintenance: []string{"tools/"}}
	content, err := json.Marshal(policy)
	if err != nil {
		t.Fatal(err)
	}
	for name, data := range map[string][]byte{"crewbook.json": []byte(layout), "LICENSE": []byte("licence\n"), "SKILL.md": []byte("fixture instructions are never executed\n"), "tools/package-policy.json": content} {
		if err = os.WriteFile(filepath.Join(root, name), data, 0644); err != nil {
			t.Fatal(err)
		}
	}
	return root
}
func invoke(t *testing.T, arguments ...string) (string, string, error) {
	t.Helper()
	var output, diagnostics bytes.Buffer
	err := run(arguments, &output, &diagnostics)
	return output.String(), diagnostics.String(), err
}
func TestSourceCLI(t *testing.T) {
	root := sourceFixture(t)
	if _, _, err := invoke(t, "check", "--root", root); err == nil {
		t.Fatal("missing saved inventory accepted")
	}
	output, _, err := invoke(t, "inventory", "--root", root)
	if err != nil || !strings.HasSuffix(output, "\n") {
		t.Fatal("inventory output", err)
	}
	if _, _, err = invoke(t, "update", "--root", root); err != nil {
		t.Fatal(err)
	}
	saved, err := os.ReadFile(filepath.Join(root, "tools/package.sha256"))
	if err != nil || string(saved) != output {
		t.Fatal("update differs from inventory", err)
	}
	stdout, stderr, err := invoke(t, "check", "--root", root)
	if err != nil || stdout != "" || !strings.Contains(stderr, "runtime compatibility not established") {
		t.Fatal("check failed or claimed runtime support", err, stdout, stderr)
	}
	destination := filepath.Join(root, "tools/export")
	if _, _, err = invoke(t, "export", "--root", root, "--dest", destination); err != nil {
		t.Fatal(err)
	}
	if _, err = os.Stat(filepath.Join(destination, "tools")); !os.IsNotExist(err) {
		t.Fatal("export included tooling")
	}
	if err = os.WriteFile(filepath.Join(root, "SKILL.md"), []byte("tampered"), 0644); err != nil {
		t.Fatal(err)
	}
	if _, _, err = invoke(t, "check", "--root", root); err == nil {
		t.Fatal("tamper accepted")
	}
	if _, _, err = invoke(t, "export", "--root", root, "--dest", filepath.Join(root, "tools/tampered")); err == nil {
		t.Fatal("tampered export accepted")
	}
}
func TestRuntimeCLIHonestMissingManifest(t *testing.T) {
	root := sourceFixture(t)
	for _, command := range []string{"runtime-check", "lock"} {
		t.Run(command, func(t *testing.T) {
			output, _, err := invoke(t, command, "--root", root)
			if err == nil || !strings.Contains(err.Error(), "missing workharbor.json") || output != "" {
				t.Fatal("missing manifest not explicit", output, err)
			}
		})
	}
}
func TestCLIErrors(t *testing.T) {
	for _, arguments := range [][]string{nil, {"unknown"}, {"check"}, {"check", "--root", "."}, {"check", "--unknown"}, {"inventory", "--root", "/nonexistent", "extra"}} {
		if _, _, err := invoke(t, arguments...); err == nil {
			t.Fatal("invalid invocation succeeded", arguments)
		}
	}
}

func TestUpdateRejectsOutputCollisions(t *testing.T) {
	for _, name := range []string{"SKILL.md", "skill.md", "crewbook.json", "LICENSE", "workharbor.json", "tools/package-policy.json", "tools/export-policy.json", "tools/maintenance.go", "tools/linked.sha256", "tools/hardlinked.sha256", "alias/SKILL.md", "tools/parent-alias/out.sha256"} {
		t.Run(name, func(t *testing.T) {
			root := sourceFixture(t)
			if _, _, err := invoke(t, "update", "--root", root); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(root, "workharbor.json"), []byte("{}\n"), 0644); err != nil {
				t.Fatal(err)
			}
			for _, file := range []string{"tools/export-policy.json", "tools/maintenance.go"} {
				if err := os.WriteFile(filepath.Join(root, file), []byte("protected metadata\n"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			if err := os.Symlink(filepath.Join(root, "SKILL.md"), filepath.Join(root, "tools/linked.sha256")); err != nil {
				t.Fatal(err)
			}
			if err := os.Link(filepath.Join(root, "tools/export-policy.json"), filepath.Join(root, "tools/hardlinked.sha256")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink(root, filepath.Join(root, "tools/parent-alias")); err != nil {
				t.Fatal(err)
			}
			inventory, err := os.ReadFile(filepath.Join(root, "tools/package.sha256"))
			if err != nil {
				t.Fatal(err)
			}
			protected := []string{"SKILL.md", "crewbook.json", "LICENSE", "workharbor.json", "tools/package-policy.json", "tools/export-policy.json", "tools/maintenance.go", "tools/package.sha256"}
			before := map[string][]byte{}
			for _, file := range protected {
				content, err := os.ReadFile(filepath.Join(root, file))
				if err != nil {
					t.Fatal(err)
				}
				before[file] = content
			}
			target := filepath.Join(root, name)
			if name == "alias/SKILL.md" {
				parent, err := filepath.EvalSymlinks(t.TempDir())
				if err != nil {
					t.Fatal(err)
				}
				alias := filepath.Join(parent, "alias")
				if err = os.Symlink(root, alias); err != nil {
					t.Fatal(err)
				}
				target = filepath.Join(alias, "SKILL.md")
			}
			output, _, err := invoke(t, "update", "--root", root, "--inventory", target)
			if err == nil || output != "" {
				t.Fatal("output collision succeeded", output, err)
			}
			for _, file := range protected {
				after, err := os.ReadFile(filepath.Join(root, file))
				if err != nil || !bytes.Equal(before[file], after) {
					t.Fatal("protected file changed", file, err)
				}
			}
			if !bytes.Equal(inventory, before["tools/package.sha256"]) {
				t.Fatal("inventory fixture drift")
			}
		})
	}
}

func TestUpdateRejectsNoncanonicalRootWithoutMutation(t *testing.T) {
	root := sourceFixture(t)
	parent, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	alias := filepath.Join(parent, "alias")
	if err = os.Symlink(root, alias); err != nil {
		t.Fatal(err)
	}
	for _, source := range []string{".", root + "/.", alias} {
		target := filepath.Join(parent, "new.inventory")
		if _, _, err = invoke(t, "update", "--root", source, "--inventory", target); err == nil {
			t.Fatal("noncanonical source accepted", source)
		}
		if _, err = os.Lstat(target); !os.IsNotExist(err) {
			t.Fatal("inventory created on invalid root", err)
		}
	}
}

func TestUpdateCustomInventory(t *testing.T) {
	root := sourceFixture(t)
	external, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	expected, _, err := invoke(t, "inventory", "--root", root)
	if err != nil {
		t.Fatal(err)
	}
	for _, target := range []string{filepath.Join(root, "tools/package.sha256"), filepath.Join(root, "tools/custom.sha256"), filepath.Join(external, "custom.inventory")} {
		for attempt := 0; attempt < 2; attempt++ {
			if _, _, err = invoke(t, "update", "--root", root, "--inventory", target); err != nil {
				t.Fatal("legitimate output refused", target, err)
			}
			content, err := os.ReadFile(target)
			if err != nil || string(content) != expected {
				t.Fatal("custom inventory differs", err)
			}
			if _, _, err = invoke(t, "check", "--root", root, "--inventory", target); err != nil {
				t.Fatal(err)
			}
		}
	}
}
