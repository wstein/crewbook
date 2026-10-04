package cicheck

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestSecretScanner(t *testing.T) {
	scanner := os.Getenv("GITLEAKS_TEST_BINARY")
	if scanner == "" {
		t.Skip("set GITLEAKS_TEST_BINARY to the pinned scanner for offline scanner fixtures")
	}
	absolute, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	source, err := filepath.EvalSymlinks(absolute)
	if err != nil {
		t.Fatal(err)
	}
	config, err := os.ReadFile(filepath.Join(source, "tools/gitleaks.toml"))
	if err != nil {
		t.Fatal(err)
	}
	environment := []string{
		"PATH=" + os.Getenv("PATH"), "GIT_CONFIG_SYSTEM=/dev/null", "GIT_CONFIG_GLOBAL=/dev/null",
		"TMPDIR=" + os.TempDir(),
		"GIT_TERMINAL_PROMPT=0", "GIT_CONFIG_COUNT=1", "GIT_CONFIG_KEY_0=credential.helper", "GIT_CONFIG_VALUE_0=",
		"SSH_AUTH_SOCK=", "GIT_SSH_COMMAND=ssh -oBatchMode=yes -oIdentityAgent=none",
		"GIT_AUTHOR_NAME=Scanner Fixture", "GIT_AUTHOR_EMAIL=fixture@example.invalid",
		"GIT_COMMITTER_NAME=Scanner Fixture", "GIT_COMMITTER_EMAIL=fixture@example.invalid",
	}
	marker := "gh" + "p_" + "aK9mQ2vB8cR5" + "xT1nL7pD4sF6" + "jH3wZ0uE9yG2"
	for _, variant := range []string{"clean", "empty", "history", "tree", "message"} {
		t.Run(variant, func(t *testing.T) {
			root, err := filepath.EvalSymlinks(t.TempDir())
			if err != nil {
				t.Fatal(err)
			}
			write := func(name, content string) {
				t.Helper()
				filename := filepath.Join(root, name)
				if err := os.MkdirAll(filepath.Dir(filename), 0755); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filename, []byte(content), 0600); err != nil {
					t.Fatal(err)
				}
			}
			git := func(arguments ...string) {
				t.Helper()
				command := exec.Command("git", arguments...)
				command.Dir, command.Env = root, environment
				if err := command.Run(); err != nil {
					t.Fatalf("isolated fixture Git failed: %v", err)
				}
			}
			git("init", "--quiet")
			write("tools/gitleaks.toml", string(config))
			write("clean.txt", "offline scanner fixture\n")
			if variant == "history" {
				write("history.txt", marker+"\n")
			}
			if variant != "empty" {
				git("add", ".")
				message := "offline fixture\n"
				if variant == "message" {
					message += marker + "\n"
				}
				messageFile := filepath.Join(t.TempDir(), "message")
				if err := os.WriteFile(messageFile, []byte(message), 0600); err != nil {
					t.Fatal(err)
				}
				git("commit", "--quiet", "-F", messageFile)
			}
			if variant == "history" {
				git("rm", "--quiet", "history.txt")
				git("commit", "--quiet", "-m", "remove fixture marker")
			}
			if variant == "tree" {
				write("untracked.txt", marker+"\n")
			}
			command := exec.Command("bash", filepath.Join(source, "tools/scan-secrets.sh"), root, scanner)
			command.Env = environment
			output, err := command.CombinedOutput()
			if strings.Contains(string(output), marker) {
				t.Fatal("scanner did not redact the synthetic marker")
			}
			if variant == "clean" {
				if err != nil || !strings.Contains(string(output), "nonempty full history") {
					t.Fatalf("clean scan failed: %v", err)
				}
			} else if exit, ok := err.(*exec.ExitError); !ok || exit.ExitCode() != 1 {
				t.Fatalf("expected nonzero scanner rejection for %s: %v", variant, err)
			}
		})
	}
}
