// Command crewbook-package maintains the reviewed crewbook text artifact.
package main

import (
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/wstein/crewbook/internal/packagefmt"
)

type provider struct {
	Bindings      []packagefmt.Binding `json:"bindings"`
	ProjectInputs []string             `json:"project_inputs"`
}

func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, "crewbook-package:", err)
		os.Exit(1)
	}
}
func run(arguments []string, output, diagnostics io.Writer) error {
	if len(arguments) == 0 {
		return errors.New("usage: crewbook-package check|inventory|update|export|runtime-check|lock [flags]")
	}
	command := arguments[0]
	switch command {
	case "check", "inventory", "update", "export", "runtime-check", "lock":
	default:
		return fmt.Errorf("unknown command %q", command)
	}
	flags := flag.NewFlagSet(command, flag.ContinueOnError)
	flags.SetOutput(diagnostics)
	root := flags.String("root", "", "canonical package source root (required)")
	policyPath := flags.String("policy", "", "maintenance policy (default <root>/tools/package-policy.json)")
	inventoryPath := flags.String("inventory", "", "inventory file (default <root>/tools/package.sha256)")
	destination := flags.String("dest", "", "new export destination")
	pinPath := flags.String("pin", "", "external reviewed six-field v1 pin")
	providerPath := flags.String("provider", "", "trusted external supported bindings/project inputs JSON")
	source := flags.String("source", "", "repository identity for lock")
	revision := flags.String("commit", "", "full reviewed commit for lock")
	identity := flags.String("identity", "crewbook", "package identity for lock")
	if err := flags.Parse(arguments[1:]); err != nil {
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("unexpected positional arguments")
	}
	if *root == "" {
		return errors.New("--root is required; no cwd fallback")
	}
	if *policyPath == "" {
		*policyPath = filepath.Join(*root, "tools/package-policy.json")
	}
	if *inventoryPath == "" {
		*inventoryPath = filepath.Join(*root, "tools/package.sha256")
	}
	policy, err := packagefmt.LoadPolicy(*policyPath)
	if err != nil {
		return fmt.Errorf("policy: %w", err)
	}
	snapshot, err := packagefmt.Scan(*root, policy)
	if err != nil {
		return err
	}
	encoded, err := packagefmt.Encode(snapshot.Files)
	if err != nil {
		return err
	}
	switch command {
	case "inventory":
		_, err = output.Write(encoded)
		return err
	case "update":
		if err = packagefmt.CheckLayout(snapshot); err != nil {
			return err
		}
		return writeInventory(*inventoryPath, encoded)
	case "check", "export":
		expected, err := packagefmt.ReadRegular(*inventoryPath, packagefmt.MaxInventoryBytes)
		if err != nil {
			return fmt.Errorf("inventory: %w", err)
		}
		if err = packagefmt.Check(snapshot, expected); err != nil {
			return err
		}
		if err = packagefmt.CheckLayout(snapshot); err != nil {
			return err
		}
		if command == "export" {
			if *destination == "" {
				return errors.New("export requires --dest")
			}
			return packagefmt.Export(snapshot, *destination)
		}
		fmt.Fprintln(diagnostics, "source content and inventory valid; runtime compatibility not established")
		return nil
	case "runtime-check", "lock":
		if len(snapshot.Manifest) == 0 {
			return packagefmt.RuntimeCheck(snapshot, packagefmt.Pin{}, nil, nil)
		}
		if *providerPath == "" {
			return errors.New("--provider requires independently trusted native version/model/effort support and confirmed project inputs")
		}
		var support provider
		data, err := packagefmt.ReadRegular(*providerPath, packagefmt.MaxManifestBytes)
		if err != nil {
			return err
		}
		if err = packagefmt.Decode(data, &support); err != nil {
			return err
		}
		var pin packagefmt.Pin
		if command == "lock" {
			pin = packagefmt.Pin{Identity: *identity, Source: *source, Commit: *revision, ManifestSHA256: packagefmt.Digest(snapshot.Manifest), InventorySHA256: packagefmt.Digest(encoded), ContractVersion: 1}
		} else {
			if *pinPath == "" {
				return errors.New("runtime-check requires --pin from an external reviewed operator lock")
			}
			data, err = packagefmt.ReadRegular(*pinPath, packagefmt.MaxManifestBytes)
			if err != nil {
				return err
			}
			if err = packagefmt.Decode(data, &pin); err != nil {
				return err
			}
		}
		if err = packagefmt.RuntimeCheck(snapshot, pin, support.Bindings, support.ProjectInputs); err != nil {
			return err
		}
		if command == "lock" {
			return packagefmt.WriteJSON(output, pin)
		}
		fmt.Fprintln(diagnostics, "package matches external pin and supplied provider assertions; live client loading is not measured by this command")
		return nil
	}
	return errors.New("unreachable command")
}

func writeInventory(filename string, content []byte) error {
	if info, err := os.Lstat(filename); err == nil {
		if !info.Mode().IsRegular() {
			return errors.New("inventory destination must be a regular file")
		}
		if _, err = packagefmt.ReadRegular(filename, packagefmt.MaxInventoryBytes); err != nil {
			return err
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	temporary, err := os.CreateTemp(filepath.Dir(filename), ".inventory-")
	if err != nil {
		return err
	}
	name := temporary.Name()
	defer os.Remove(name)
	if _, err = temporary.Write(content); err != nil {
		temporary.Close()
		return err
	}
	if err = temporary.Chmod(0644); err != nil {
		temporary.Close()
		return err
	}
	if err = temporary.Close(); err != nil {
		return err
	}
	return os.Rename(name, filename)
}
