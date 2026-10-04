package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/wstein/crewbook/internal/packagefmt"
)

func TestDistributionPolicyAgreement(t *testing.T) {
	source, err := packagefmt.LoadPolicy("../../tools/package-policy.json")
	if err != nil {
		t.Fatal(err)
	}
	exported, err := packagefmt.LoadPolicy("../../tools/export-policy.json")
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(source.Distributed, exported.Distributed) || len(exported.Maintenance) != 0 {
		t.Fatal("export policy must preserve the source's exact distributed set without maintenance exclusions")
	}
}

func TestStagedExportInventory(t *testing.T) {
	root := sourceFixture(t)
	layoutBytes, err := os.ReadFile(filepath.Join(root, "crewbook.json"))
	if err != nil {
		t.Fatal(err)
	}
	var layout packagefmt.Layout
	if err = json.Unmarshal(layoutBytes, &layout); err != nil {
		t.Fatal(err)
	}
	layout.Entrypoints.Roles = []string{".agents/role.md"}
	layout.Entrypoints.ClaudeAgents = []string{".claude/agents/profile.md"}
	layoutBytes, err = json.Marshal(layout)
	if err != nil {
		t.Fatal(err)
	}
	policy := packagefmt.Policy{Version: 1, Distributed: []string{
		".agents/role.md", ".claude/agents/profile.md", "LICENSE", "SKILL.md", "crewbook.json",
	}, Maintenance: []string{"tools/"}}
	policyBytes, err := json.Marshal(policy)
	if err != nil {
		t.Fatal(err)
	}
	exportPolicy := policy
	exportPolicy.Maintenance = []string{}
	exportPolicyBytes, err := json.Marshal(exportPolicy)
	if err != nil {
		t.Fatal(err)
	}
	for name, data := range map[string][]byte{
		"crewbook.json":              layoutBytes,
		".agents/role.md":            []byte("fixture role text\n"),
		".claude/agents/profile.md":  []byte("fixture profile text\n"),
		"tools/package-policy.json":  policyBytes,
		"tools/export-policy.json":   exportPolicyBytes,
		"tools/maintenance-only.txt": []byte("must not be distributed\n"),
	} {
		filename := filepath.Join(root, filepath.FromSlash(name))
		if err = os.MkdirAll(filepath.Dir(filename), 0755); err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(filename, data, 0644); err != nil {
			t.Fatal(err)
		}
	}
	if _, _, err = invoke(t, "update", "--root", root); err != nil {
		t.Fatal(err)
	}
	inventoryPath := filepath.Join(root, "tools/package.sha256")
	first, err := os.ReadFile(inventoryPath)
	if err != nil {
		t.Fatal(err)
	}
	if _, _, err = invoke(t, "update", "--root", root); err != nil {
		t.Fatal(err)
	}
	second, err := os.ReadFile(inventoryPath)
	if err != nil || !bytes.Equal(first, second) {
		t.Fatal("unchanged default update must be deterministic", err)
	}
	lines := strings.Split(strings.TrimSuffix(string(first), "\n"), "\n")
	paths := make([]string, 0, len(lines))
	for _, line := range lines {
		fields := strings.SplitN(line, "  ", 2)
		if len(fields) != 2 || len(fields[0]) != 64 {
			t.Fatal("invalid inventory encoding", line)
		}
		paths = append(paths, fields[1])
	}
	if !strings.HasSuffix(string(first), "\n") || !sort.StringsAreSorted(paths) || !reflect.DeepEqual(paths, policy.Distributed) {
		t.Fatal("inventory must cover dot-directories in ASCII path order with final LF")
	}
	exportParent, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	policyPath := filepath.Join(root, "tools/export-policy.json")
	check := func(directory string) error {
		_, _, checkErr := invoke(t, "check", "--root", directory, "--policy", policyPath, "--inventory", inventoryPath)
		return checkErr
	}
	for _, name := range []string{"first", "second"} {
		destination := filepath.Join(exportParent, name)
		if _, _, err = invoke(t, "export", "--root", root, "--dest", destination); err != nil {
			t.Fatal(err)
		}
		if name == "second" {
			relocated := filepath.Join(exportParent, "relocated")
			if err = os.Rename(destination, relocated); err != nil {
				t.Fatal(err)
			}
			destination = relocated
		}
		if err = check(destination); err != nil {
			t.Fatal("relocated export must pass exact validation", err)
		}
		encoded, _, inventoryErr := invoke(t, "inventory", "--root", destination, "--policy", policyPath)
		if inventoryErr != nil || encoded != string(first) {
			t.Fatal("export inventory differs from source", inventoryErr)
		}
		if _, err = os.Stat(filepath.Join(destination, "tools")); !os.IsNotExist(err) {
			t.Fatal("maintenance content was exported")
		}
		for _, command := range []string{"runtime-check", "lock"} {
			output, _, runtimeErr := invoke(t, command, "--root", destination, "--policy", policyPath)
			if runtimeErr == nil || !strings.Contains(runtimeErr.Error(), "missing workharbor.json") || output != "" {
				t.Fatal("content export must not become a runtime-compatible package", command, runtimeErr)
			}
		}
	}
	cases := []struct {
		name   string
		mutate func(string) error
	}{
		{"missing-dot-resource", func(directory string) error {
			return os.Remove(filepath.Join(directory, ".agents/role.md"))
		}},
		{"unexpected-dot-resource", func(directory string) error {
			return os.WriteFile(filepath.Join(directory, ".extra"), []byte("extra\n"), 0644)
		}},
		{"tampered", func(directory string) error {
			filename := filepath.Join(directory, "SKILL.md")
			if chmodErr := os.Chmod(filename, 0600); chmodErr != nil {
				return chmodErr
			}
			return os.WriteFile(filename, []byte("tampered\n"), 0600)
		}},
		{"unexpected-maintenance", func(directory string) error {
			if mkdirErr := os.Mkdir(filepath.Join(directory, "tools"), 0755); mkdirErr != nil {
				return mkdirErr
			}
			return os.WriteFile(filepath.Join(directory, "tools/injected.txt"), []byte("extra\n"), 0644)
		}},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			destination := filepath.Join(exportParent, test.name)
			if _, _, exportErr := invoke(t, "export", "--root", root, "--dest", destination); exportErr != nil {
				t.Fatal(exportErr)
			}
			if mutateErr := test.mutate(destination); mutateErr != nil {
				t.Fatal(mutateErr)
			}
			if checkErr := check(destination); checkErr == nil {
				t.Fatal("invalid staged export accepted")
			}
		})
	}
}
