// Fixture data only. Normalization belongs to the service, not one caller.
package fixture
import "strings"
func Service(name string, denied bool) string {
    if denied { return "DENIED" }
    return strings.TrimSpace(name)
}
func JSON(name string, denied bool) string { return Service(name, denied) }
func CLI(name string, denied bool) string { return Service(name, denied) }
