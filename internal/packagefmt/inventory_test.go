package packagefmt

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestWriteInventoryProtectsSource(t *testing.T) {
	root, policy := fixture(t)
	write(t, root, "tools/policy.json", []byte("policy"))
	write(t, root, "tools/code.go", []byte("package tools\n"))
	snapshot := scan(t, root, policy)
	encoded, err := Encode(snapshot.Files)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"SKILL.md", "LICENSE", "tools/policy.json", "tools/code.go"} {
		t.Run(name, func(t *testing.T) {
			filename := filepath.Join(root, name)
			before, err := os.ReadFile(filename)
			if err != nil {
				t.Fatal(err)
			}
			if err = WriteInventory(root, filename, filepath.Join(root, "tools/policy.json"), policy, encoded); err == nil {
				t.Fatal("source collision accepted")
			}
			after, err := os.ReadFile(filename)
			if err != nil || !bytes.Equal(before, after) {
				t.Fatal("source changed", err)
			}
		})
	}
}

func TestWriteInventoryRejectsNoncanonicalRoot(t *testing.T) {
	root, policy := fixture(t)
	encoded, err := Encode(scan(t, root, policy).Files)
	if err != nil {
		t.Fatal(err)
	}
	parent, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	alias := filepath.Join(parent, "alias")
	if err = os.Symlink(root, alias); err != nil {
		t.Fatal(err)
	}
	for _, source := range []string{".", root + "/.", alias} {
		output := filepath.Join(parent, "new.sha256")
		if err = WriteInventory(source, output, filepath.Join(root, "tools/policy.json"), policy, encoded); err == nil {
			t.Fatal("noncanonical root accepted", source)
		}
		if _, err = os.Lstat(output); !os.IsNotExist(err) {
			t.Fatal("output created", err)
		}
	}
}

func TestWriteInventoryCannotExcludeItsOwnOutput(t *testing.T) {
	root, policy := fixture(t)
	encoded, err := Encode(scan(t, root, policy).Files)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.Mkdir(filepath.Join(root, "tools"), 0755); err != nil {
		t.Fatal(err)
	}
	policy.Maintenance = nil
	target := filepath.Join(root, "tools/custom.sha256")
	if err = WriteInventory(root, target, filepath.Join(root, "policy.json"), policy, encoded); err == nil {
		t.Fatal("output gained an implicit maintenance exemption")
	}
	if _, err = os.Lstat(target); !os.IsNotExist(err) {
		t.Fatal("unexpected output", err)
	}
}
