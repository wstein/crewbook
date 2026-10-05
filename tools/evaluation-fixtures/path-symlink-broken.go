// Fixture data only. Ordinary-case validation misses the trust boundary.
package fixture
func Allowed(name string, symlinks map[string]bool) bool { return name != "" }
