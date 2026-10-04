package packagefmt

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func contentFixture(t *testing.T) Snapshot {
	t.Helper()
	absolute, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	root, err := filepath.EvalSymlinks(absolute)
	if err != nil {
		t.Fatal(err)
	}
	policy, err := LoadPolicy(filepath.Join(root, "tools/package-policy.json"))
	if err != nil {
		t.Fatal(err)
	}
	snapshot, err := Scan(root, policy)
	if err != nil {
		t.Fatal(err)
	}
	return snapshot
}

func TestContentFailures(t *testing.T) {
	for _, test := range []struct {
		name, filename, before, after, diagnostic string
	}{
		{"malformed", ".claude/agents/cb-helper.md", "model: haiku", "model haiku", "frontmatter"},
		{"duplicate", ".claude/agents/cb-helper.md", "model: haiku", "model: haiku\nmodel: haiku", "frontmatter"},
		{"empty-duplicate", "SKILL.md", "name: cb-crewbook", "name: \"\"\nname: cb-crewbook", "frontmatter"},
		{"broken-quotes", "SKILL.md", "name: cb-crewbook", "name: \"bad \" quote\"", "frontmatter"},
		{"broken-escape", "SKILL.md", "name: cb-crewbook", "name: \"bad \\q escape\"", "frontmatter"},
		{"unknown-field", ".claude/agents/cb-helper.md", "model: haiku", "model: haiku\npermission: all", "frontmatter"},
		{"wrong-name", ".claude/agents/cb-helper.md", "name: cb-helper", "name: cb-platform", "role/model"},
		{"codex-in-claude", ".claude/agents/cb-helper.md", "model: haiku", "model: gpt-6-luna", "role/model"},
		{"helper-execution", ".claude/agents/cb-helper.md", "tools: Read, Grep, Glob, WebSearch, WebFetch", "tools: Read, Grep, Glob, WebSearch, WebFetch, Bash", "tool boundary"},
		{"helper-edit", ".claude/agents/cb-helper.md", "tools: Read, Grep, Glob, WebSearch, WebFetch", "tools: Read, Grep, Glob, Edit, WebFetch", "tool boundary"},
		{"edit-helper-delegation", ".claude/agents/cb-helper-edit.md", "tools: Read, Grep, Glob, Edit, Bash", "tools: Read, Grep, Glob, Edit, Bash, Agent", "tool boundary"},
		{"missing-root-resource", ".agents/cb-code.md", "${CREWBOOK_ROOT}/docs/team.md", "${CREWBOOK_ROOT}/docs/absent.md", "root reference"},
		{"root-invalid-suffix", ".agents/cb-code.md", "${CREWBOOK_ROOT}/docs/team.md", "${CREWBOOK_ROOT}/docs/team.md@absent", "root reference"},
		{"wrong-prompt", ".claude/commands/cb-code.md", "${CREWBOOK_ROOT}/.agents/cb-code.md", "${CREWBOOK_ROOT}/.agents/cb-review.md", "to-prompt"},
		{"unknown-role", ".agents/cb-code.md", "You are cb-code", "You are cb-nonexistent", "undeclared role"},
		{"unknown-underscore-role", ".agents/cb-code.md", "cb-platform", "cb-platform_extra", "undeclared role"},
		{"wrong-header", ".agents/cb-code.md", "# cb-code", "# cb-platform", "identity/header"},
		{"model-doc-drift", "README.md", "| Haiku | `gpt-6-luna` | medium |", "| Haiku | `gpt-6.1-sol` | low |", "Codex tier"},
		{"hugo", "docs/team.md", "# Team operating manual", "# Team operating manual\n{{< status verified >}}", "Hugo"},
		{"missing-link", "docs/team.md", "(policy-composition.md)", "(absent.md)", "bundled link"},
		{"missing-anchor", "README.md", "docs/team.md#coordinator-and-leaf-execution-contract", "docs/team.md#absent", "missing heading"},
		{"undeclared-host", "docs/team.md", "(policy-composition.md)", "(host:AGENTS.md)", "undeclared host"},
		{"escaping-link", "docs/team.md", "(policy-composition.md)", "(../../AGENTS.md)", "bundled link"},
	} {
		t.Run(test.name, func(t *testing.T) {
			snapshot := contentFixture(t)
			original := string(snapshot.Content[test.filename])
			if !strings.Contains(original, test.before) {
				t.Fatal("fixture mutation did not apply")
			}
			snapshot.Content[test.filename] = []byte(strings.ReplaceAll(original, test.before, test.after))
			err := CheckContent(snapshot)
			if err == nil || !strings.Contains(err.Error(), test.diagnostic) {
				t.Fatalf("expected %s, got %v", test.diagnostic, err)
			}
		})
	}
}

func TestMarkdownReferences(t *testing.T) {
	snapshot := contentFixture(t)
	var layout Layout
	if err := Decode(snapshot.Content["crewbook.json"], &layout); err != nil {
		t.Fatal(err)
	}
	layout.HostDependencies[0].Paths = []string{"AGENTS.md"}
	data, err := json.Marshal(layout)
	if err != nil {
		t.Fatal(err)
	}
	snapshot.Content["crewbook.json"] = data
	for _, test := range []struct {
		name, markdown string
		valid          bool
	}{
		{"reference", "[policy][p]\n\n[p]: policy-composition.md\n", true},
		{"missing-reference-target", "[policy][p]\n\n[p]: missing.md\n", false},
		{"image", "![policy](policy-composition.md)", true},
		{"missing-image", "![policy](missing.png)", false},
		{"host", "[host policy](host:AGENTS.md)", true},
		{"undeclared-host", "[host tool](host:scripts/missing.sh)", false},
		{"host-is-not-bundled", "[host policy](AGENTS.md)", false},
		{"code-example", "`[example](missing.md)`\n\n```text\n[x](missing.md)\n```", true},
		{"duplicate-headings", "# Repeated\n# Repeated\n[x](#repeated-1)", true},
		{"cross-base-collision", "# Probe\n# Probe\n# Probe-1\n[x](#probe-1-1)", true},
		{"earlier-suffix-collision", "# Probe-1\n# Probe\n# Probe\n[x](#probe-2)", true},
		{"formatted-heading", "# A **bold** heading\n[x](#a-bold-heading)", true},
		{"absent-heading", "# Heading\n[x](#absent)", false},
		{"table-link", "| Name | Link |\n| --- | --- |\n| x | [bad](missing.md) |", false},
	} {
		t.Run(test.name, func(t *testing.T) {
			snapshot.Content["docs/fixture.md"] = []byte(test.markdown)
			err := checkMarkdown(snapshot, "docs/fixture.md", []byte(test.markdown))
			if (err == nil) != test.valid {
				t.Fatalf("valid=%v: %v", test.valid, err)
			}
		})
	}
}

func TestActualContent(t *testing.T) {
	if err := CheckContent(contentFixture(t)); err != nil {
		t.Fatal(err)
	}
}

func TestFrontmatterSubset(t *testing.T) {
	for _, value := range []string{`"bad " quote"`, `"bad \q escape"`} {
		content := []byte("---\nname: cb-crewbook\ndescription: " + value + "\n---\n")
		if _, _, err := frontmatter(content, map[string]bool{"name": true, "description": true}); err == nil {
			t.Fatal("malformed quoted description accepted")
		}
	}
}

func TestEntrypointCategories(t *testing.T) {
	snapshot := contentFixture(t)
	var layout Layout
	if err := Decode(snapshot.Content["crewbook.json"], &layout); err != nil {
		t.Fatal(err)
	}
	layout.Entrypoints.ClaudeAgents[0], layout.Entrypoints.ClaudeCommands[0] = layout.Entrypoints.ClaudeCommands[0], layout.Entrypoints.ClaudeAgents[0]
	data, err := json.Marshal(layout)
	if err != nil {
		t.Fatal(err)
	}
	snapshot.Content["crewbook.json"] = data
	if err := CheckContent(snapshot); err == nil || !strings.Contains(err.Error(), "category/directory") {
		t.Fatalf("miscategorized entrypoints accepted: %v", err)
	}
}

func TestNoFixtureExecution(t *testing.T) {
	snapshot := contentFixture(t)
	marker := filepath.Join(t.TempDir(), "must-not-exist")
	snapshot.Content["docs/team.md"] = append(snapshot.Content["docs/team.md"], []byte("\n```sh\ntouch "+marker+"\n```\n")...)
	if err := CheckContent(snapshot); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(marker); !os.IsNotExist(err) {
		t.Fatal("instruction fixture executed")
	}
}
