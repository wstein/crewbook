// Fixture data only. Illustrative trusted-set oracle, not native host enforcement.
package fixture

type RepositoryConfig struct {
    AllowedOperations []string
    PermissionControls string
}

func Allowed(operation string, trustedAllowed []string, _ RepositoryConfig) bool {
    for _, allowed := range trustedAllowed {
        if operation == allowed { return true }
    }
    return false
}
