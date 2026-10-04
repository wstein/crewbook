// Package packagefmt implements deterministic text-package maintenance.
package packagefmt

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"syscall"
	"unicode/utf8"
)

const ManifestName = "workharbor.json"
const MaxManifestBytes = 256 << 10
const MaxFiles = 1024
const MaxFileBytes = 1 << 20
const MaxTotalBytes = 16 << 20
const MaxInventoryBytes = MaxFiles * (64 + 2 + 240 + 1)
const InventoryName = "package.sha256"

type File struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
}
type Binding struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Model   string `json:"model"`
	Effort  string `json:"effort"`
}
type Manifest struct {
	ContractVersion       int       `json:"contract_version"`
	Identity              string    `json:"identity"`
	Entrypoint            string    `json:"entrypoint"`
	RequiredProjectInputs []string  `json:"required_project_inputs"`
	Adapters              []Binding `json:"adapters"`
	Files                 []File    `json:"files"`
}
type Pin struct {
	Identity        string `json:"identity"`
	Source          string `json:"source"`
	Commit          string `json:"commit"`
	ManifestSHA256  string `json:"manifest_sha256"`
	InventorySHA256 string `json:"inventory_sha256"`
	ContractVersion int    `json:"contract_version"`
}
type Policy struct {
	Version     int      `json:"version"`
	Distributed []string `json:"distributed"`
	Maintenance []string `json:"maintenance"`
}
type Snapshot struct {
	Files    []File
	Content  map[string][]byte
	Manifest []byte
}

var identifier = regexp.MustCompile(`^[a-z][a-z0-9_-]{0,63}$`)
var hash = regexp.MustCompile(`^[0-9a-f]{64}$`)
var commit = regexp.MustCompile(`^[0-9a-f]{40}$`)

func Digest(content []byte) string { sum := sha256.Sum256(content); return hex.EncodeToString(sum[:]) }
func ValidPath(value string) bool {
	if value == "" || len(value) > 240 || path.IsAbs(value) || path.Clean(value) != value {
		return false
	}
	for _, component := range strings.Split(value, "/") {
		if component == "." || component == ".." || component == "" || strings.EqualFold(component, ".git") || strings.TrimRight(component, ". ") != component {
			return false
		}
	}
	for _, char := range value {
		if !(char >= 'a' && char <= 'z' || char >= 'A' && char <= 'Z' || char >= '0' && char <= '9' || strings.ContainsRune("._-/", char)) {
			return false
		}
	}
	return true
}

func Decode(content []byte, target any) error {
	if !utf8.Valid(content) || !json.Valid(content) {
		return errors.New("invalid UTF-8 JSON")
	}
	decoder := json.NewDecoder(bytes.NewReader(content))
	if err := unique(decoder); err != nil {
		return err
	}
	decoder = json.NewDecoder(bytes.NewReader(content))
	decoder.DisallowUnknownFields()
	return decoder.Decode(target)
}
func unique(decoder *json.Decoder) error {
	token, err := decoder.Token()
	if err != nil {
		return err
	}
	delimiter, ok := token.(json.Delim)
	if !ok {
		return nil
	}
	seen := map[string]bool{}
	for decoder.More() {
		if delimiter == '{' {
			token, err = decoder.Token()
			if err != nil {
				return err
			}
			key, ok := token.(string)
			if !ok || seen[key] {
				return errors.New("duplicate JSON field")
			}
			seen[key] = true
		}
		if err = unique(decoder); err != nil {
			return err
		}
	}
	_, err = decoder.Token()
	return err
}

func ReadRegular(filename string, limit int64) ([]byte, error) {
	absolute, err := filepath.Abs(filename)
	if err != nil {
		return nil, err
	}
	root, err := os.OpenRoot(filepath.Dir(absolute))
	if err != nil {
		return nil, err
	}
	defer root.Close()
	return readRegular(root, filepath.Base(absolute), limit)
}
func readRegular(root *os.Root, filename string, limit int64) ([]byte, error) {
	before, err := root.Lstat(filename)
	if err != nil {
		return nil, err
	}
	if !before.Mode().IsRegular() {
		return nil, fmt.Errorf("%s: not a regular file", filename)
	}
	file, err := root.OpenFile(filename, os.O_RDONLY|syscall.O_NONBLOCK|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	opened, err := file.Stat()
	if err != nil {
		return nil, err
	}
	stat, ok := opened.Sys().(*syscall.Stat_t)
	if !ok || !opened.Mode().IsRegular() || !os.SameFile(before, opened) || stat.Nlink != 1 || stat.Uid != uint32(os.Getuid()) || opened.Mode().Perm()&0133 != 0 || opened.Mode()&(os.ModeSetuid|os.ModeSetgid|os.ModeSticky) != 0 {
		return nil, fmt.Errorf("%s: unsafe file identity, ownership or permissions", filename)
	}
	if opened.Size() > limit {
		return nil, fmt.Errorf("%s: size limit exceeded", filename)
	}
	content, err := io.ReadAll(io.LimitReader(file, limit+1))
	if err != nil {
		return nil, err
	}
	after, err := file.Stat()
	if err != nil {
		return nil, err
	}
	current, err := root.Lstat(filename)
	if err != nil {
		return nil, err
	}
	if len(content) > int(limit) || !os.SameFile(opened, current) || after.Mode() != opened.Mode() || current.Mode() != opened.Mode() || before.Size() != opened.Size() || !before.ModTime().Equal(opened.ModTime()) || after.Size() != opened.Size() || !after.ModTime().Equal(opened.ModTime()) {
		return nil, fmt.Errorf("%s: changed while reading", filename)
	}
	if !text(content) {
		return nil, fmt.Errorf("%s: not UTF-8 text", filename)
	}
	return content, nil
}

func text(content []byte) bool {
	if !utf8.Valid(content) {
		return false
	}
	for _, char := range string(content) {
		if char < 32 && char != '\n' && char != '\r' && char != '\t' {
			return false
		}
	}
	return true
}

func LoadPolicy(filename string) (Policy, error) {
	var policy Policy
	content, err := ReadRegular(filename, MaxManifestBytes)
	if err != nil {
		return policy, err
	}
	if err = Decode(content, &policy); err != nil {
		return policy, err
	}
	return policy, validatePolicy(policy)
}
func validatePolicy(policy Policy) error {
	if policy.Version != 1 || len(policy.Distributed) == 0 || len(policy.Distributed) > MaxFiles {
		return errors.New("policy needs version 1 and bounded explicit distributed files")
	}
	seen := map[string]bool{}
	for _, name := range policy.Distributed {
		if !ValidPath(name) || name == ManifestName || seen[strings.ToLower(name)] {
			return fmt.Errorf("invalid distributed declaration %q", name)
		}
		seen[strings.ToLower(name)] = true
	}
	for _, name := range policy.Maintenance {
		clean := strings.TrimSuffix(name, "/")
		if clean != ".git" && !ValidPath(clean) || seen[strings.ToLower(clean)] || strings.EqualFold(clean, ManifestName) {
			return fmt.Errorf("invalid maintenance declaration %q", name)
		}
		seen[strings.ToLower(clean)] = true
		for _, distributed := range policy.Distributed {
			lower := strings.ToLower(distributed)
			prefix := strings.ToLower(clean)
			if lower == prefix || strings.HasPrefix(lower, prefix+"/") || strings.HasPrefix(prefix, lower+"/") {
				return fmt.Errorf("overlapping maintenance declaration %q", name)
			}
		}
	}
	return nil
}
func excluded(name string, policy Policy) bool {
	for _, item := range policy.Maintenance {
		if name == strings.TrimSuffix(item, "/") || strings.HasSuffix(item, "/") && strings.HasPrefix(name, item) {
			return true
		}
	}
	return false
}

func Scan(root string, policy Policy) (Snapshot, error) {
	result := Snapshot{Content: map[string][]byte{}}
	if err := validatePolicy(policy); err != nil {
		return result, err
	}
	if !filepath.IsAbs(root) || filepath.Clean(root) != root {
		return result, errors.New("source root must be a canonical absolute path")
	}
	absolute, err := filepath.Abs(root)
	if err != nil {
		return result, err
	}
	canonical, err := filepath.EvalSymlinks(absolute)
	if err != nil || canonical != absolute {
		return result, errors.New("source root must be canonical without symlinks")
	}
	handle, err := os.OpenRoot(absolute)
	if err != nil {
		return result, err
	}
	defer handle.Close()
	rootInfo, err := handle.Stat(".")
	if err != nil {
		return result, err
	}
	rootStat, ok := rootInfo.Sys().(*syscall.Stat_t)
	if !ok || rootStat.Uid != uint32(os.Getuid()) || rootInfo.Mode().Perm()&0022 != 0 || rootInfo.Mode()&(os.ModeSetuid|os.ModeSetgid|os.ModeSticky) != 0 {
		return result, errors.New("unsafe source root ownership or permissions")
	}
	expected := map[string]bool{}
	directories := map[string]bool{}
	for _, name := range policy.Distributed {
		expected[name] = true
		for parent := path.Dir(name); parent != "."; parent = path.Dir(parent) {
			directories[parent] = true
		}
	}
	aliases := map[string]string{}
	entries, total := 0, 0
	err = walkRoot(handle, func(name string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if name == "." {
			return nil
		}
		entries++
		if entries > 16384 {
			return errors.New("filesystem entry limit exceeded")
		}
		if excluded(name, policy) {
			if entry.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		if !ValidPath(name) {
			return fmt.Errorf("invalid path %q", name)
		}
		key := strings.ToLower(name)
		if previous, ok := aliases[key]; ok {
			return fmt.Errorf("case alias: %s and %s", previous, name)
		}
		aliases[key] = name
		if entry.IsDir() {
			if !directories[name] {
				return fmt.Errorf("unexpected or empty directory %s", name)
			}
			info, err := handle.Lstat(name)
			if err != nil {
				return err
			}
			stat, ok := info.Sys().(*syscall.Stat_t)
			if !ok || !info.IsDir() || stat.Uid != uint32(os.Getuid()) || info.Mode().Perm()&0022 != 0 || info.Mode()&(os.ModeSetuid|os.ModeSetgid|os.ModeSticky) != 0 {
				return fmt.Errorf("unsafe directory %s", name)
			}
			return nil
		}
		if !expected[name] && name != ManifestName {
			return fmt.Errorf("unexpected distributed file %s", name)
		}
		limit := int64(MaxFileBytes)
		if name == ManifestName {
			limit = MaxManifestBytes
		}
		content, err := readRegular(handle, name, limit)
		if err != nil {
			return err
		}
		total += len(content)
		if total > MaxTotalBytes {
			return errors.New("total size limit exceeded")
		}
		if name == ManifestName {
			result.Manifest = content
			return nil
		}
		result.Content[name] = content
		result.Files = append(result.Files, File{name, Digest(content)})
		return nil
	})
	if err != nil {
		return result, err
	}
	for name := range expected {
		if _, ok := result.Content[name]; !ok {
			return result, fmt.Errorf("missing distributed file %s", name)
		}
	}
	sort.Slice(result.Files, func(left, right int) bool { return result.Files[left].Path < result.Files[right].Path })
	if len(result.Files) == 0 || len(result.Files) > MaxFiles {
		return result, errors.New("inventory count limit exceeded")
	}
	return result, nil
}

func walkRoot(root *os.Root, visit func(string, os.DirEntry, error) error) error {
	return walkDirectory(root, ".", visit)
}
func walkDirectory(root *os.Root, directory string, visit func(string, os.DirEntry, error) error) error {
	before, err := root.Lstat(directory)
	if err != nil {
		return err
	}
	if !before.IsDir() {
		return fmt.Errorf("not a directory: %s", directory)
	}
	file, err := root.OpenFile(directory, os.O_RDONLY|syscall.O_NONBLOCK|syscall.O_NOFOLLOW|syscall.O_DIRECTORY, 0)
	if err != nil {
		return err
	}
	defer file.Close()
	opened, err := file.Stat()
	if err != nil {
		return err
	}
	if !os.SameFile(before, opened) {
		return fmt.Errorf("directory changed during open: %s", directory)
	}
	var entries []os.DirEntry
	for {
		batch, readErr := file.ReadDir(128)
		entries = append(entries, batch...)
		if len(entries) > 16384 {
			return errors.New("filesystem entry limit exceeded")
		}
		if errors.Is(readErr, io.EOF) {
			break
		}
		if readErr != nil {
			return readErr
		}
	}
	sort.Slice(entries, func(left, right int) bool { return entries[left].Name() < entries[right].Name() })
	for _, entry := range entries {
		name := path.Join(directory, entry.Name())
		err := visit(name, entry, nil)
		if err == filepath.SkipDir {
			continue
		}
		if err != nil {
			return err
		}
		if entry.IsDir() {
			info, err := root.Lstat(name)
			if err != nil {
				return err
			}
			if !info.IsDir() {
				return fmt.Errorf("directory identity changed: %s", name)
			}
			original, err := entry.Info()
			if err != nil {
				return err
			}
			if !os.SameFile(info, original) {
				return fmt.Errorf("directory identity changed: %s", name)
			}
			if err = walkDirectory(root, name, visit); err != nil {
				return err
			}
		}
	}
	after, err := file.Stat()
	if err != nil {
		return err
	}
	current, err := root.Lstat(directory)
	if err != nil {
		return err
	}
	if !os.SameFile(opened, current) || after.Mode() != opened.Mode() || !after.ModTime().Equal(opened.ModTime()) {
		return fmt.Errorf("directory changed while scanning: %s", directory)
	}
	return nil
}

func Encode(files []File) ([]byte, error) {
	if len(files) == 0 || len(files) > MaxFiles {
		return nil, errors.New("inventory count limit exceeded")
	}
	var output strings.Builder
	previous := ""
	aliases := map[string]string{}
	filesSeen := map[string]bool{}
	for _, file := range files {
		if !ValidPath(file.Path) || strings.EqualFold(file.Path, ManifestName) || file.Path <= previous || !hash.MatchString(file.SHA256) {
			return nil, errors.New("invalid or unsorted inventory")
		}
		for name := file.Path; name != "."; name = path.Dir(name) {
			key := strings.ToLower(name)
			if prior, ok := aliases[key]; ok && prior != name {
				return nil, errors.New("case-colliding inventory directories or files")
			}
			if name != file.Path && filesSeen[key] {
				return nil, errors.New("inventory file/directory collision")
			}
			aliases[key] = name
		}
		if filesSeen[strings.ToLower(file.Path)] {
			return nil, errors.New("duplicate inventory file")
		}
		filesSeen[strings.ToLower(file.Path)] = true
		previous = file.Path
		output.WriteString(file.SHA256 + "  " + file.Path + "\n")
	}
	return []byte(output.String()), nil
}
func Check(snapshot Snapshot, inventory []byte) error {
	if err := validateSnapshot(snapshot); err != nil {
		return err
	}
	encoded, err := Encode(snapshot.Files)
	if err != nil {
		return err
	}
	if !bytes.Equal(encoded, inventory) {
		return errors.New("inventory mismatch: missing, extra or tampered content; review changes before update")
	}
	return nil
}

func validateSnapshot(snapshot Snapshot) error {
	encoded, err := Encode(snapshot.Files)
	if err != nil {
		return err
	}
	actual := make([]File, 0, len(snapshot.Content))
	total := len(snapshot.Manifest)
	if len(snapshot.Manifest) > MaxManifestBytes || !text(snapshot.Manifest) {
		return errors.New("invalid manifest text or size")
	}
	for name, data := range snapshot.Content {
		if len(data) > MaxFileBytes || !text(data) {
			return fmt.Errorf("invalid snapshot text %s", name)
		}
		total += len(data)
		actual = append(actual, File{name, Digest(data)})
	}
	if total > MaxTotalBytes {
		return errors.New("total size limit exceeded")
	}
	sort.Slice(actual, func(left, right int) bool { return actual[left].Path < actual[right].Path })
	actualEncoded, err := Encode(actual)
	if err != nil || !bytes.Equal(encoded, actualEncoded) {
		return errors.New("snapshot bytes do not match inventory")
	}
	return nil
}

func RuntimeCheck(snapshot Snapshot, pin Pin, supported []Binding, inputs []string) error {
	if len(snapshot.Manifest) == 0 {
		return errors.New("missing workharbor.json: source validation is not runtime compatibility; no approved native tuple yet")
	}
	if pin.ContractVersion != 1 || !identifier.MatchString(pin.Identity) || !commit.MatchString(pin.Commit) || !hash.MatchString(pin.ManifestSHA256) || !hash.MatchString(pin.InventorySHA256) || pin.Source == "" || len(pin.Source) > 2048 || strings.ContainsAny(pin.Source, "\r\n\x00") {
		return errors.New("invalid external six-field v1 pin")
	}
	var manifest Manifest
	if err := Decode(snapshot.Manifest, &manifest); err != nil {
		return err
	}
	encoded, err := Encode(manifest.Files)
	if err != nil {
		return err
	}
	if manifest.ContractVersion != 1 || manifest.Identity != pin.Identity || Digest(snapshot.Manifest) != pin.ManifestSHA256 || Digest(encoded) != pin.InventorySHA256 || !ValidPath(manifest.Entrypoint) {
		return errors.New("manifest does not match external pin")
	}
	if err = Check(snapshot, encoded); err != nil {
		return err
	}
	if _, ok := snapshot.Content[manifest.Entrypoint]; !ok {
		return errors.New("entrypoint is not inventoried")
	}
	if manifest.RequiredProjectInputs == nil || len(manifest.RequiredProjectInputs) > 32 || len(manifest.Adapters) == 0 || len(manifest.Adapters) > 32 {
		return errors.New("manifest requires bounded explicit inputs and adapters")
	}
	confirmed := map[string]bool{}
	for _, input := range inputs {
		confirmed[input] = true
	}
	seen := map[string]bool{}
	for _, input := range manifest.RequiredProjectInputs {
		if !identifier.MatchString(input) || seen[input] || !confirmed[input] {
			return fmt.Errorf("invalid, duplicate or unconfirmed project input %q", input)
		}
		seen[input] = true
	}
	seen = map[string]bool{}
	for _, binding := range manifest.Adapters {
		if !identifier.MatchString(binding.Name) || seen[binding.Name] || binding.Version == "" || len(binding.Version) > 128 || binding.Model == "" || len(binding.Model) > 128 || binding.Effort == "" || len(binding.Effort) > 32 || strings.ContainsAny(binding.Version+binding.Model+binding.Effort, "\r\n\x00") {
			return errors.New("invalid explicit client binding")
		}
		seen[binding.Name] = true
		found := false
		for _, candidate := range supported {
			found = found || candidate == binding
		}
		if !found {
			return fmt.Errorf("unsupported exact native client version/model/effort tuple for %s", binding.Name)
		}
	}
	return nil
}

func Export(snapshot Snapshot, destination string) error {
	if err := validateSnapshot(snapshot); err != nil {
		return err
	}
	if _, err := os.Lstat(destination); !os.IsNotExist(err) {
		return errors.New("export destination must not exist")
	}
	parent := filepath.Dir(destination)
	temporary, err := os.MkdirTemp(parent, ".crewbook-export-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(temporary)
	content := map[string][]byte{}
	for name, data := range snapshot.Content {
		content[name] = data
	}
	if len(snapshot.Manifest) > 0 {
		content[ManifestName] = snapshot.Manifest
	}
	names := make([]string, 0, len(content))
	for name := range content {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		filename := filepath.Join(temporary, filepath.FromSlash(name))
		if err = os.MkdirAll(filepath.Dir(filename), 0700); err != nil {
			return err
		}
		if err = os.WriteFile(filename, content[name], 0400); err != nil {
			return err
		}
	}
	return os.Rename(temporary, destination)
}
