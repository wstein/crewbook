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
