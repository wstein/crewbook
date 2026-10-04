package packagefmt

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func inventoryLines(content []byte) error {
	if len(content) == 0 || len(content) > MaxInventoryBytes || content[len(content)-1] != '\n' {
		return errors.New("inventory must contain canonical hash lines with a final LF")
	}
	lines := strings.Split(string(content[:len(content)-1]), "\n")
	files := make([]File, 0, len(lines))
	for _, line := range lines {
		if len(line) < 67 || line[64:66] != "  " {
			return errors.New("not a canonical inventory file")
		}
		files = append(files, File{Path: line[66:], SHA256: line[:64]})
	}
	encoded, err := Encode(files)
	if err != nil {
		return err
	}
	if !bytes.Equal(encoded, content) {
		return errors.New("not a canonical inventory file")
	}
	return nil
}

func WriteInventory(root, filename, policyPath string, policy Policy, content []byte) error {
	if !filepath.IsAbs(root) || filepath.Clean(root) != root {
		return errors.New("inventory source root must be a canonical absolute path")
	}
	if err := validatePolicy(policy); err != nil {
		return err
	}
	if err := inventoryLines(content); err != nil {
		return err
	}
	source, err := filepath.EvalSymlinks(root)
	if err != nil {
		return err
	}
	if source != root {
		return errors.New("inventory source root must not have symlink aliases")
	}
	absolute, err := filepath.Abs(filename)
	if err != nil {
		return err
	}
	parent := filepath.Dir(absolute)
	canonicalParent, err := filepath.EvalSymlinks(parent)
	if err != nil {
		return fmt.Errorf("inventory parent: %w", err)
	}
	if canonicalParent != parent {
		return errors.New("inventory output parent must be canonical without symlink aliases")
	}
	relative, err := filepath.Rel(source, absolute)
	if err != nil {
		return err
	}
	inside := relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator))
	if inside && (relative == "tools" || !strings.HasPrefix(strings.ToLower(filepath.ToSlash(relative)), "tools/")) {
		return errors.New("inventory output inside source must be under tools/")
	}
	if inside && !excluded(filepath.ToSlash(relative), policy) {
		return errors.New("inventory output must already be excluded by the maintenance policy")
	}
	protected := append([]string{ManifestName}, policy.Distributed...)
	for _, name := range protected {
		protectedPath := filepath.Join(source, filepath.FromSlash(name))
		if err = rejectCollision(absolute, protectedPath); err != nil {
			return err
		}
	}
	if err = rejectCollision(absolute, policyPath); err != nil {
		return err
	}
	before, err := os.Lstat(parent)
	if err != nil {
		return err
	}
	if !before.IsDir() {
		return errors.New("inventory parent is not a directory")
	}
	handle, err := os.OpenRoot(parent)
	if err != nil {
		return err
	}
	defer handle.Close()
	opened, err := handle.Stat(".")
	if err != nil {
		return err
	}
	if !os.SameFile(before, opened) {
		return errors.New("inventory parent changed while opening")
	}
	leaf := filepath.Base(absolute)
	validateTarget := func() error {
		info, err := handle.Lstat(leaf)
		if os.IsNotExist(err) {
			return nil
		}
		if err != nil {
			return err
		}
		if !info.Mode().IsRegular() {
			return errors.New("inventory destination must be a regular file without symlink aliases")
		}
		existing, err := readRegular(handle, leaf, MaxInventoryBytes)
		if err != nil {
			return err
		}
		if err = inventoryLines(existing); err != nil {
			return fmt.Errorf("refusing to overwrite non-inventory file: %w", err)
		}
		return nil
	}
	if err = validateTarget(); err != nil {
		return err
	}
	var random [16]byte
	if _, err = rand.Read(random[:]); err != nil {
		return err
	}
	temporary := ".inventory-" + hex.EncodeToString(random[:])
	file, err := handle.OpenFile(temporary, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	defer handle.Remove(temporary)
	if _, err = file.Write(content); err != nil {
		file.Close()
		return err
	}
	if err = file.Chmod(0644); err != nil {
		file.Close()
		return err
	}
	if err = file.Close(); err != nil {
		return err
	}
	if err = validateTarget(); err != nil {
		return err
	}
	return handle.Rename(temporary, leaf)
}

func rejectCollision(output, protected string) error {
	absolute, err := filepath.Abs(protected)
	if err != nil {
		return err
	}
	canonicalParent, err := filepath.EvalSymlinks(filepath.Dir(absolute))
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	canonical := filepath.Join(canonicalParent, filepath.Base(absolute))
	if strings.EqualFold(output, canonical) {
		return fmt.Errorf("inventory output collides with protected source or policy file %s", protected)
	}
	outputInfo, err := os.Stat(output)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	protectedInfo, err := os.Stat(absolute)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	if os.SameFile(outputInfo, protectedInfo) {
		return fmt.Errorf("inventory output aliases protected source or policy file %s", protected)
	}
	return nil
}
