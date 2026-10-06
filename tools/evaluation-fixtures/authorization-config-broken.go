// Fixture data only. Deliberately trusts repository-controlled permission claims.
package fixture

type RepositoryConfig struct {
    AllowedOperations []string
    PermissionControls string
}

func Allowed(operation string, trustedAllowed []string, config RepositoryConfig) bool {
    if config.PermissionControls == "disabled" { return true }
    for _, allowed := range config.AllowedOperations {
        if operation == allowed { return true }
    }
    for _, allowed := range trustedAllowed {
        if operation == allowed { return true }
    }
    return false
}
