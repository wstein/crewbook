// Fixture data only. JSON and CLI call Service unchanged.
package fixture
func Service(name string, denied bool) string {
    if denied { return name } // Swallows adapter denial.
    return name // Shared normalization missing.
}
func JSON(name string, denied bool) string { return Service(name, denied) }
func CLI(name string, denied bool) string { return Service(name, denied) }
