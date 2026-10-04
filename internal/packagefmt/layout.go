package packagefmt

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
)

type Layout struct {
	SchemaVersion int    `json:"schema_version"`
	Name          string `json:"name"`
	License       string `json:"license"`
	Entrypoints   struct {
		Skill          string   `json:"skill"`
		Roles          []string `json:"roles"`
		ClaudeAgents   []string `json:"claude_agents"`
		ClaudeCommands []string `json:"claude_commands"`
	} `json:"entrypoints"`
	Resources        []string `json:"resources"`
	HostDependencies []struct {
		Name   string   `json:"name"`
		Scope  string   `json:"scope"`
		Status string   `json:"status"`
		Paths  []string `json:"paths,omitempty"`
	} `json:"host_dependencies"`
}

func CheckLayout(snapshot Snapshot) error {
	var layout Layout
	if err := Decode(snapshot.Content["crewbook.json"], &layout); err != nil {
		return fmt.Errorf("crewbook.json: %w", err)
	}
	if layout.SchemaVersion != 1 || !identifier.MatchString(layout.Name) || layout.License != "EUPL-1.2" || layout.Entrypoints.Roles == nil || layout.Entrypoints.ClaudeAgents == nil || layout.Entrypoints.ClaudeCommands == nil || layout.Resources == nil || layout.HostDependencies == nil {
		return errors.New("incomplete crewbook v1 layout")
	}
	required := []string{layout.Entrypoints.Skill}
	required = append(required, layout.Entrypoints.Roles...)
	required = append(required, layout.Entrypoints.ClaudeAgents...)
	required = append(required, layout.Entrypoints.ClaudeCommands...)
	required = append(required, layout.Resources...)
	seen := map[string]bool{}
	for _, name := range required {
		if !ValidPath(name) || seen[name] {
			return fmt.Errorf("invalid or duplicate layout path %q", name)
		}
		seen[name] = true
		if _, ok := snapshot.Content[name]; !ok {
			return fmt.Errorf("missing layout resource %s", name)
		}
	}
	for name := range snapshot.Content {
		if !seen[name] {
			return fmt.Errorf("distributed file not declared in crewbook.json: %s", name)
		}
	}
	for _, dependency := range layout.HostDependencies {
		if dependency.Name == "" || dependency.Scope == "" || dependency.Status == "" {
			return errors.New("host dependencies require name, scope and status")
		}
		for _, resource := range dependency.Paths {
			if !ValidPath(resource) || seen[resource] {
				return errors.New("host dependency paths must be explicit, unique and outside the bundled set")
			}
			seen[resource] = true
		}
	}
	return nil
}

func WriteJSON(output io.Writer, value any) error {
	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}
