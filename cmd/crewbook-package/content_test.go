package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestContentProcess(t *testing.T) {
	if os.Getenv("CREWBOOK_TEST_PROCESS") != "1" {
		return
	}
	os.Args = []string{"crewbook-package", "check", "--root", os.Getenv("CREWBOOK_TEST_ROOT")}
	main()
}

func TestContentExitStatus(t *testing.T) {
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	for _, test := range []struct {
		name, text, diagnostic string
		valid                  bool
	}{
		{"valid", "---\nname: cb-crewbook\ndescription: offline fixture\n---\n", "", true},
		{"metadata", "---\nname cb-crewbook\ndescription: fixture\n---\n", "frontmatter", false},
		{"missing-resource", "---\nname: cb-crewbook\ndescription: fixture\n---\nRead ${CREWBOOK_ROOT}/missing.md\n", "root reference", false},
		{"missing-link", "---\nname: cb-crewbook\ndescription: fixture\n---\n[x](missing.md)\n", "bundled link", false},
	} {
		t.Run(test.name, func(t *testing.T) {
			root := sourceFixture(t)
			if err := os.WriteFile(filepath.Join(root, "SKILL.md"), []byte(test.text), 0644); err != nil {
				t.Fatal(err)
			}
			if _, _, err := invoke(t, "update", "--root", root); err != nil {
				t.Fatal(err)
			}
			command := exec.Command(executable, "-test.run=^TestContentProcess$")
			command.Env = []string{"CREWBOOK_TEST_PROCESS=1", "CREWBOOK_TEST_ROOT=" + root}
			output, err := command.CombinedOutput()
			if test.valid {
				if err != nil {
					t.Fatalf("valid process failed: %v %s", err, output)
				}
			} else {
				exit, ok := err.(*exec.ExitError)
				if !ok || exit.ExitCode() != 1 || !strings.Contains(string(output), test.diagnostic) {
					t.Fatalf("expected content failure exit 1 (%s): %v %s", test.diagnostic, err, output)
				}
			}
		})
	}
}
