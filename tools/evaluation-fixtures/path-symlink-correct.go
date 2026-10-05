// Fixture data only. Static tree oracle; this is not a race-safe file opener.
package fixture
import "strings"
func Allowed(name string, symlinks map[string]bool) bool {
    if name == "" || strings.HasPrefix(name, "/") { return false }
    var parts []string
    for _, part := range strings.Split(name, "/") {
        if part == ".." { return false }
        if part == "" || part == "." { continue }
        parts = append(parts, part)
        if symlinks[strings.Join(parts, "/")] { return false }
    }
    return len(parts) > 0
}
