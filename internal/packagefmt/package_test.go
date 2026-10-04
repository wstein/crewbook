package packagefmt

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

func fixture(t *testing.T) (string, Policy) {
	t.Helper()
	root, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	policy := Policy{Version: 1, Distributed: []string{".agents/role.md", "LICENSE", "SKILL.md"}, Maintenance: []string{"tools/"}}
	for _, name := range policy.Distributed {
		write(t, root, name, []byte("text "+name+"\n"))
	}
	return root, policy
}
func write(t *testing.T, root, name string, content []byte) {
	t.Helper()
	filename := filepath.Join(root, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(filename), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filename, content, 0644); err != nil {
		t.Fatal(err)
	}
}
func scan(t *testing.T, root string, policy Policy) Snapshot {
	t.Helper()
	snapshot, err := Scan(root, policy)
	if err != nil {
		t.Fatal(err)
	}
	return snapshot
}

func TestDeterministicInventoryAndExport(t *testing.T) {
	root, policy := fixture(t)
	write(t, root, "tools/source.go", []byte("excluded\n"))
	first := scan(t, root, policy)
	second := scan(t, root, policy)
	encoded, err := Encode(first.Files)
	if err != nil {
		t.Fatal(err)
	}
	again, err := Encode(second.Files)
	if err != nil || !bytes.Equal(encoded, again) {
		t.Fatal("nondeterministic inventory", err)
	}
	expected := Digest([]byte("text .agents/role.md\n")) + "  .agents/role.md\n" + Digest([]byte("text LICENSE\n")) + "  LICENSE\n" + Digest([]byte("text SKILL.md\n")) + "  SKILL.md\n"
	if string(encoded) != expected {
		t.Fatalf("encoding differs: %q", encoded)
	}
	if err = Check(first, encoded); err != nil {
		t.Fatal(err)
	}
	destination := filepath.Join(root, "tools", "export")
	if err = Export(first, destination); err != nil {
		t.Fatal(err)
	}
	exported := scan(t, destination, Policy{Version: 1, Distributed: policy.Distributed})
	exportedBytes, err := Encode(exported.Files)
	if err != nil || !bytes.Equal(encoded, exportedBytes) {
		t.Fatal("export drift", err)
	}
	if _, err = os.Stat(filepath.Join(destination, "tools")); !os.IsNotExist(err) {
		t.Fatal("maintenance tooling exported")
	}
	if err = Export(first, destination); err == nil {
		t.Fatal("overwrote existing export")
	}
}

func TestScanRejectsUnsafeFiles(t *testing.T) {
	cases := []struct {
		name   string
		mutate func(*testing.T, string)
	}{
		{"missing", func(t *testing.T, root string) {
			if err := os.Remove(filepath.Join(root, "SKILL.md")); err != nil {
				t.Fatal(err)
			}
		}},
		{"extra-dotfile", func(t *testing.T, root string) { write(t, root, ".hidden", []byte("extra")) }},
		{"empty-directory", func(t *testing.T, root string) {
			if err := os.Mkdir(filepath.Join(root, "empty"), 0755); err != nil {
				t.Fatal(err)
			}
		}},
		{"symlink", func(t *testing.T, root string) {
			if err := os.Remove(filepath.Join(root, "SKILL.md")); err != nil {
				t.Fatal(err)
			}
			if err := os.Symlink("LICENSE", filepath.Join(root, "SKILL.md")); err != nil {
				t.Fatal(err)
			}
		}},
		{"hardlink", func(t *testing.T, root string) {
			if err := os.Remove(filepath.Join(root, "SKILL.md")); err != nil {
				t.Fatal(err)
			}
			if err := os.Link(filepath.Join(root, "LICENSE"), filepath.Join(root, "SKILL.md")); err != nil {
				t.Fatal(err)
			}
		}},
		{"executable", func(t *testing.T, root string) {
			if err := os.Chmod(filepath.Join(root, "SKILL.md"), 0755); err != nil {
				t.Fatal(err)
			}
		}},
		{"world-writable", func(t *testing.T, root string) {
			if err := os.Chmod(filepath.Join(root, "SKILL.md"), 0666); err != nil {
				t.Fatal(err)
			}
		}},
		{"binary", func(t *testing.T, root string) { write(t, root, "SKILL.md", []byte{0xff}) }},
		{"nul", func(t *testing.T, root string) { write(t, root, "SKILL.md", []byte{0}) }},
		{"oversize", func(t *testing.T, root string) {
			write(t, root, "SKILL.md", bytes.Repeat([]byte("a"), MaxFileBytes+1))
		}},
		{"fifo", func(t *testing.T, root string) {
			filename := filepath.Join(root, "SKILL.md")
			if err := os.Remove(filename); err != nil {
				t.Fatal(err)
			}
			if err := syscall.Mkfifo(filename, 0600); err != nil {
				t.Fatal(err)
			}
		}},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			root, policy := fixture(t)
			test.mutate(t, root)
			if _, err := Scan(root, policy); err == nil {
				t.Fatal("unsafe source accepted")
			}
		})
	}
}

func TestTamperedInventory(t *testing.T) {
	root, policy := fixture(t)
	baseline := scan(t, root, policy)
	encoded, err := Encode(baseline.Files)
	if err != nil {
		t.Fatal(err)
	}
	write(t, root, "SKILL.md", []byte("changed\n"))
	if err = Check(scan(t, root, policy), encoded); err == nil {
		t.Fatal("tampered content accepted")
	}
}
func TestPathsAndAliases(t *testing.T) {
	for _, name := range []string{"../escape", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a.", "a/.GIT/b", "a/é", "a/", "a b", strings.Repeat("a", 241)} {
		t.Run(name, func(t *testing.T) {
			if ValidPath(name) {
				t.Fatal("invalid path accepted")
			}
		})
	}
	digest := Digest([]byte("fixture"))
	for _, files := range [][]File{
		{{"a", digest}, {"A", digest}},
		{{"A", digest}, {"a", digest}},
		{{"a", strings.ToUpper(digest)}},
		{{ManifestName, digest}},
		{{"A/one", digest}, {"a/two", digest}},
		{{"a", digest}, {"a/child", digest}},
	} {
		if _, err := Encode(files); err == nil {
			t.Fatal("invalid inventory accepted", files)
		}
	}
	root, policy := fixture(t)
	policy.Distributed = append(policy.Distributed, "../escape")
	if _, err := Scan(root, policy); err == nil {
		t.Fatal("escaping policy accepted")
	}
	_, policy = fixture(t)
	policy.Maintenance = append(policy.Maintenance, ".agents/")
	if _, err := Scan(root, policy); err == nil {
		t.Fatal("overlapping exclusions accepted")
	}
}
func TestStrictJSON(t *testing.T) {
	for _, content := range []string{`{"version":1,"version":1}`, `{"version":1,"unknown":true}`, `null`, `{} {}`} {
		var policy Policy
		err := Decode([]byte(content), &policy)
		if err == nil {
			err = validatePolicy(policy)
		}
		if err == nil {
			t.Fatal("invalid policy accepted", content)
		}
	}
}
func runtimeFixture(t *testing.T) (Snapshot, Pin, Binding) {
	t.Helper()
	root, policy := fixture(t)
	snapshot := scan(t, root, policy)
	binding := Binding{Name: "claude-code", Version: "fixture-only opaque version", Model: "fixture-only-model", Effort: "fixture-only-effort"}
	manifest := Manifest{ContractVersion: 1, Identity: "crewbook", Entrypoint: "SKILL.md", RequiredProjectInputs: []string{"project-policy"}, Adapters: []Binding{binding}, Files: snapshot.Files}
	content, err := json.Marshal(manifest)
	if err != nil {
		t.Fatal(err)
	}
	snapshot.Manifest = content
	encoded, err := Encode(snapshot.Files)
	if err != nil {
		t.Fatal(err)
	}
	pin := Pin{Identity: "crewbook", Source: "fixture-only-source", Commit: strings.Repeat("a", 40), ManifestSHA256: Digest(content), InventorySHA256: Digest(encoded), ContractVersion: 1}
	return snapshot, pin, binding
}
func TestRuntimeContract(t *testing.T) {
	snapshot, pin, binding := runtimeFixture(t)
	if err := RuntimeCheck(snapshot, pin, []Binding{binding}, []string{"project-policy"}); err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name   string
		mutate func(*Snapshot, *Pin, *Binding)
		inputs []string
	}{
		{"missing-manifest", func(snapshot *Snapshot, _ *Pin, _ *Binding) { snapshot.Manifest = nil }, []string{"project-policy"}},
		{"wrong-manifest-hash", func(_ *Snapshot, pin *Pin, _ *Binding) { pin.ManifestSHA256 = strings.Repeat("0", 64) }, []string{"project-policy"}},
		{"wrong-version", func(_ *Snapshot, _ *Pin, binding *Binding) { binding.Version = "other" }, []string{"project-policy"}},
		{"wrong-model", func(_ *Snapshot, _ *Pin, binding *Binding) { binding.Model = "other" }, []string{"project-policy"}},
		{"wrong-effort", func(_ *Snapshot, _ *Pin, binding *Binding) { binding.Effort = "other" }, []string{"project-policy"}},
		{"missing-input", func(_ *Snapshot, _ *Pin, _ *Binding) {}, nil},
		{"long-identity", func(_ *Snapshot, pin *Pin, _ *Binding) { pin.Identity = strings.Repeat("a", 65) }, []string{"project-policy"}},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			snapshot, pin, binding := runtimeFixture(t)
			test.mutate(&snapshot, &pin, &binding)
			if err := RuntimeCheck(snapshot, pin, []Binding{binding}, test.inputs); err == nil {
				t.Fatal("invalid runtime contract accepted")
			}
		})
	}
	if err := RuntimeCheck(snapshot, pin, nil, []string{"project-policy"}); err == nil {
		t.Fatal("missing provider accepted")
	}
	content, err := json.Marshal(pin)
	if err != nil {
		t.Fatal(err)
	}
	var fields map[string]any
	if err = json.Unmarshal(content, &fields); err != nil || len(fields) != 6 {
		t.Fatal("six-field pin changed", err)
	}
}
func TestExportRejectsForgedSnapshot(t *testing.T) {
	root, policy := fixture(t)
	snapshot := scan(t, root, policy)
	snapshot.Content["../escape"] = []byte("bad")
	if err := Export(snapshot, filepath.Join(root, "export")); err == nil {
		t.Fatal("forged export accepted")
	}
}

func TestSnapshotLimits(t *testing.T) {
	files := make([]File, MaxFiles+1)
	if _, err := Encode(files); err == nil {
		t.Fatal("file-count limit not enforced")
	}
	snapshot := Snapshot{Content: map[string][]byte{}}
	for index := 0; index < 17; index++ {
		name := fmt.Sprintf("file%02d", index)
		data := bytes.Repeat([]byte("a"), MaxFileBytes)
		snapshot.Content[name] = data
		snapshot.Files = append(snapshot.Files, File{name, Digest(data)})
	}
	encoded, err := Encode(snapshot.Files)
	if err != nil {
		t.Fatal(err)
	}
	if err = Check(snapshot, encoded); err == nil {
		t.Fatal("total limit not enforced")
	}
	root, policy := fixture(t)
	write(t, root, ManifestName, bytes.Repeat([]byte("a"), MaxManifestBytes+1))
	if _, err = Scan(root, policy); err == nil {
		t.Fatal("manifest limit not enforced")
	}
}

func TestLayoutRejectsMissingUnknownAndDuplicateResources(t *testing.T) {
	base := `{"schema_version":1,"name":"crewbook","license":"EUPL-1.2","entrypoints":{"skill":"SKILL.md","roles":[],"claude_agents":[],"claude_commands":[]},"resources":["crewbook.json","LICENSE"],"host_dependencies":[]}`
	for _, test := range []struct {
		name   string
		layout string
		remove string
	}{
		{"valid", base, ""},
		{"missing-resource", base, "LICENSE"},
		{"duplicate-resource", strings.Replace(base, `"LICENSE"`, `"SKILL.md"`, 1), ""},
		{"unknown-property", strings.Replace(base, `"schema_version":1`, `"schema_version":1,"executable":"bad"`, 1), ""},
	} {
		t.Run(test.name, func(t *testing.T) {
			snapshot := Snapshot{Content: map[string][]byte{"crewbook.json": []byte(test.layout), "SKILL.md": []byte("skill"), "LICENSE": []byte("license")}}
			if test.remove != "" {
				delete(snapshot.Content, test.remove)
			}
			err := CheckLayout(snapshot)
			if (err == nil) != (test.name == "valid") {
				t.Fatal("unexpected layout result", err)
			}
		})
	}
}
