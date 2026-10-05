package packagefmt

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"path"
	"regexp"
	"sort"
	"strings"
	"unicode"

	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/ast"
	"github.com/yuin/goldmark/extension"
	markdowntext "github.com/yuin/goldmark/text"
)

var rootReference = regexp.MustCompile("\\$\\{CREWBOOK_ROOT\\}/([^\\s`\"'<>\\[\\](){},;]+)")
var roleReference = regexp.MustCompile(`\bcb-[a-z][a-z0-9_-]*\b`)

var profileModels = map[string]string{
	"cb-design": "opus", "cb-docs-reviewer": "sonnet", "cb-docs": "sonnet",
	"cb-helper-edit": "haiku", "cb-helper": "haiku", "cb-platform": "sonnet",
	"cb-reviewer": "opus", "cb-runtime": "sonnet", "cb-verify": "sonnet", "cb-worker": "sonnet",
}

var promptTargets = map[string]string{
	"cb-design": "cb-design", "cb-docs-reviewer": "cb-review", "cb-docs": "cb-docs",
	"cb-helper-edit": "cb-helper", "cb-helper": "cb-helper", "cb-platform": "cb-code",
	"cb-reviewer": "cb-review", "cb-runtime": "cb-code", "cb-verify": "cb-verify",
	"cb-code": "cb-code", "cb-desk": "cb-desk", "cb-dispatch": "cb-dispatch", "cb-review": "cb-review", "cb-delegate": "cb-helper",
}

func frontmatter(content []byte, fields map[string]bool) (map[string]string, []byte, error) {
	if !bytes.HasPrefix(content, []byte("---\n")) {
		return nil, nil, errors.New("missing frontmatter")
	}
	end := bytes.Index(content[4:], []byte("\n---\n"))
	if end < 0 {
		return nil, nil, errors.New("unterminated frontmatter")
	}
	metadata := map[string]string{}
	for _, line := range strings.Split(string(content[4:4+end]), "\n") {
		key, value, ok := strings.Cut(line, ":")
		value = strings.TrimSpace(value)
		_, exists := metadata[key]
		if !ok || !fields[key] || value == "" || exists || strings.ContainsAny(value, "\r\t") {
			return nil, nil, errors.New("frontmatter requires unique supported scalar fields")
		}
		if strings.HasPrefix(value, `"`) {
			var decoded string
			if err := json.Unmarshal([]byte(value), &decoded); err != nil {
				return nil, nil, errors.New("quoted scalar must use valid JSON string syntax")
			}
			value = decoded
		} else if strings.ContainsAny(value[:1], "{}[]&*!|>'\"") || strings.Contains(value, ": ") || strings.Contains(value, " #") {
			return nil, nil, errors.New("unsupported frontmatter scalar syntax")
		}
		metadata[key] = value
	}
	return metadata, content[4+end+5:], nil
}

func CheckContent(snapshot Snapshot) error {
	if err := CheckLayout(snapshot); err != nil {
		return err
	}
	var layout Layout
	if err := Decode(snapshot.Content["crewbook.json"], &layout); err != nil {
		return err
	}
	known := map[string]bool{"cb-crewbook": true, "cb-generic": true, "cb-workharbor": true, "cb-board": true, "cb-land": true, "cb-handover": true}
	for name := range profileModels {
		known[name] = true
	}
	for _, filename := range append(append([]string{}, layout.Entrypoints.Roles...), layout.Entrypoints.ClaudeCommands...) {
		known[strings.TrimSuffix(path.Base(filename), ".md")] = true
	}
	for _, filename := range layout.Entrypoints.Roles {
		name := strings.TrimSuffix(path.Base(filename), ".md")
		if path.Dir(filename) != ".agents" || !strings.HasPrefix(name, "cb-") || !identifier.MatchString(name) || !bytes.HasPrefix(snapshot.Content[filename], []byte("# "+name+"\n")) {
			return fmt.Errorf("%s: role identity/header mismatch", filename)
		}
	}
	for _, group := range []struct {
		directory string
		files     []string
	}{{".claude/agents", layout.Entrypoints.ClaudeAgents}, {".claude/commands", layout.Entrypoints.ClaudeCommands}} {
		for _, filename := range group.files {
			if path.Dir(filename) != group.directory {
				return fmt.Errorf("%s: entrypoint category/directory mismatch", filename)
			}
		}
	}
	metadata, _, err := frontmatter(snapshot.Content[layout.Entrypoints.Skill], map[string]bool{"name": true, "description": true})
	if err != nil || metadata["name"] != "cb-crewbook" || metadata["description"] == "" {
		return fmt.Errorf("%s: invalid skill frontmatter: %v", layout.Entrypoints.Skill, err)
	}
	for _, filename := range append(append([]string{}, layout.Entrypoints.ClaudeAgents...), layout.Entrypoints.ClaudeCommands...) {
		name := strings.TrimSuffix(path.Base(filename), ".md")
		agent := path.Dir(filename) == ".claude/agents"
		fields := map[string]bool{"description": true, "argument-hint": true}
		if agent {
			fields = map[string]bool{"name": true, "description": true, "model": true, "tools": true}
		} else if path.Dir(filename) != ".claude/commands" {
			return fmt.Errorf("%s: invalid command directory", filename)
		}
		metadata, body, err := frontmatter(snapshot.Content[filename], fields)
		if err != nil || metadata["description"] == "" || !known[name] {
			return fmt.Errorf("%s: invalid profile/command frontmatter: %v", filename, err)
		}
		if agent {
			if profileModels[name] == "" || metadata["name"] != name || metadata["model"] != profileModels[name] {
				return fmt.Errorf("%s: Claude role/model mismatch", filename)
			}
			if name == "cb-helper" || name == "cb-helper-edit" || name == "cb-reviewer" || name == "cb-docs-reviewer" {
				expected := "Glob,Grep,Read,WebFetch,WebSearch"
				if name == "cb-helper-edit" {
					expected = "Bash,Edit,Glob,Grep,Read"
				}
				if name == "cb-reviewer" || name == "cb-docs-reviewer" {
					expected = "Bash,Glob,Grep,Read,WebFetch,WebSearch"
				}
				tools := strings.Split(metadata["tools"], ",")
				for index := range tools {
					tools[index] = strings.TrimSpace(tools[index])
				}
				sort.Strings(tools)
				if strings.Join(tools, ",") != expected {
					return fmt.Errorf("%s: helper tool boundary mismatch", filename)
				}
			} else if metadata["tools"] != "" {
				return fmt.Errorf("%s: unexpected tools override", filename)
			}
		}
		if target := promptTargets[name]; target != "" {
			if !bytes.Contains(body, []byte("${CREWBOOK_ROOT}/.agents/"+target+".md")) {
				return fmt.Errorf("%s: missing command/profile-to-prompt link", filename)
			}
		}
	}
	if len(layout.Entrypoints.ClaudeAgents) > 0 {
		readme := string(snapshot.Content["README.md"])
		for _, row := range []string{"| Sonnet | `gpt-6.1-sol` | low |", "| Opus | `gpt-6.1-sol` | medium |", "| Haiku | `gpt-6-luna` | medium |"} {
			if !strings.Contains(readme, row) {
				return errors.New("README: documented Codex tier mapping missing or changed")
			}
		}
	}
	for filename, content := range snapshot.Content {
		if !strings.HasSuffix(filename, ".md") {
			continue
		}
		if bytes.Contains(content, []byte("{{<")) || bytes.Contains(content, []byte("{{%")) {
			return fmt.Errorf("%s: Hugo shortcode is not GFM", filename)
		}
		for _, match := range rootReference.FindAllSubmatch(content, -1) {
			resource := strings.TrimRight(string(match[1]), ".")
			if !ValidPath(resource) || snapshot.Content[resource] == nil {
				return fmt.Errorf("%s: missing bundled root reference %s", filename, resource)
			}
		}
		if strings.HasPrefix(filename, ".agents/") || strings.HasPrefix(filename, ".claude/") || filename == layout.Entrypoints.Skill {
			for _, name := range roleReference.FindAllString(string(content), -1) {
				if !known[name] {
					return fmt.Errorf("%s: undeclared role %s", filename, name)
				}
			}
		}
		if err := checkMarkdown(snapshot, filename, content); err != nil {
			return err
		}
	}
	return nil
}

func checkMarkdown(snapshot Snapshot, filename string, content []byte) error {
	markdown := goldmark.New(goldmark.WithExtensions(extension.GFM))
	document := markdown.Parser().Parse(markdowntext.NewReader(content))
	return ast.Walk(document, func(node ast.Node, entering bool) (ast.WalkStatus, error) {
		if !entering {
			return ast.WalkContinue, nil
		}
		var destination []byte
		switch link := node.(type) {
		case *ast.Link:
			destination = link.Destination
		case *ast.Image:
			destination = link.Destination
		default:
			return ast.WalkContinue, nil
		}
		parsed, err := url.Parse(string(destination))
		if err != nil {
			return ast.WalkStop, fmt.Errorf("%s: malformed link", filename)
		}
		if parsed.Scheme == "https" || parsed.Scheme == "http" || parsed.Scheme == "mailto" {
			return ast.WalkContinue, nil
		}
		if parsed.Scheme == "host" {
			var layout Layout
			if err := Decode(snapshot.Content["crewbook.json"], &layout); err != nil {
				return ast.WalkStop, err
			}
			for _, dependency := range layout.HostDependencies {
				for _, resource := range dependency.Paths {
					if parsed.Opaque == resource && parsed.Fragment == "" && parsed.RawQuery == "" {
						return ast.WalkContinue, nil
					}
				}
			}
			return ast.WalkStop, fmt.Errorf("%s: undeclared host dependency", filename)
		}
		if parsed.Scheme != "" || parsed.Host != "" || strings.HasPrefix(parsed.Path, "/") || parsed.RawQuery != "" {
			return ast.WalkStop, fmt.Errorf("%s: unsupported link destination", filename)
		}
		target := filename
		if parsed.Path != "" {
			target = path.Clean(path.Join(path.Dir(filename), parsed.Path))
		}
		resource, ok := snapshot.Content[target]
		if !ok || !ValidPath(target) {
			return ast.WalkStop, fmt.Errorf("%s: missing bundled link %s; host dependencies must use explicit host declarations, not package links", filename, target)
		}
		if parsed.Fragment != "" && !headingIDs(resource)[parsed.Fragment] {
			return ast.WalkStop, fmt.Errorf("%s: missing heading %s in %s", filename, parsed.Fragment, target)
		}
		return ast.WalkContinue, nil
	})
}

func headingIDs(content []byte) map[string]bool {
	markdown := goldmark.New(goldmark.WithExtensions(extension.GFM))
	document := markdown.Parser().Parse(markdowntext.NewReader(content))
	ids := map[string]bool{}
	ast.Walk(document, func(node ast.Node, entering bool) (ast.WalkStatus, error) {
		if heading, ok := node.(*ast.Heading); ok && entering {
			var label strings.Builder
			ast.Walk(heading, func(child ast.Node, entering bool) (ast.WalkStatus, error) {
				if value, ok := child.(*ast.Text); ok && entering {
					label.Write(value.Segment.Value(content))
				}
				return ast.WalkContinue, nil
			})
			var slug strings.Builder
			for _, char := range strings.ToLower(label.String()) {
				if char == ' ' {
					slug.WriteByte('-')
				} else if unicode.IsLetter(char) || unicode.IsNumber(char) || char == '-' || char == '_' {
					slug.WriteRune(char)
				}
			}
			base := slug.String()
			id := base
			for suffix := 1; ids[id]; suffix++ {
				id = fmt.Sprintf("%s-%d", base, suffix)
			}
			ids[id] = true
		}
		return ast.WalkContinue, nil
	})
	return ids
}
