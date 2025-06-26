# cline Ruleset: C# 9

## 1. Records and Immutable Data

- **MUST** use `record` types for immutable data objects and value-like behaviors.
- **ALWAYS** prefer `init` accessors for properties in records to enforce immutability.
- **NEVER** mutate record properties directly after creation; use `with` expressions when copying records.
- Serialization and deserialization of records **SHOULD** be handled with care; prefer supported serializers.

## 2. Pattern Matching Enhancements

- **REQUIRED** to use `is not null` and relational patterns for concise and expressive code when appropriate.
- Logical patterns (`and`, `or`, `not`) **SHOULD** be used to simplify complex conditional logic.
- **NEVER** use verbose or outdated pattern-matching constructs when a newer, more readable C# 9 pattern is available.

## 3. Target-Typed New Expressions

- **MUST** use target-typed `new()` expressions to eliminate redundancy when the type is clear from context.
- **NEVER** use ambiguous or unclear `new()` expressions where type inference fails or code clarity is reduced.

## 4. Top-level Programs

- **ALWAYS** use top-level statements in simple applications, scripts, or demos for clarity.
- In complex, production, or library projects, it is **MANDATORY** to use an explicit `Main` method and appropriate structure.

## 5. Init-Only Setters

- **MUST** use `init` setters for properties intended only for initialization.
- **NEVER** expose mutable setters if immutability is required.

## 6. Covariant Returns

- **REQUIRED** to override methods with covariant return types when the derived type provides extra information.
- **NEVER** violate interface contracts or the Liskov Substitution Principle with inappropriate variance.

## 7. Improved `using` Declarations

- **ALWAYS** use implicit `using` declarations to ensure proper resource disposal at the closest scope.
- **NEVER** rely solely on finalizers for releasing resources; resources **MUST** be disposed manually or via `using`.

## 8. Nullable Reference Types

- **MANDATORY** to enable nullable reference types in all new C# 9 projects.
- **MUST** accurately annotate all reference types (`?` for nullable, no annotation for non-nullable).
- **NEVER** suppress nullable warnings without a documented justification.

## 9. Safety, Readability, and Modern Syntax

- **ALWAYS** favor expression-bodied members and concise syntax enabled by C# 9.
- **MUST** use type inference (`var`) when the variable type is clear and unambiguous; otherwise, specify the type explicitly for clarity.
- File-scoped namespaces **SHOULD** be adopted for all files where supported.

## 10. Version and Compatibility

- C# 9 features **MUST** target .NET 5.0 or later; **NEVER** use in pre-.NET 5 projects.
- **REQUIRED** to verify project and library compatibility before using C# 9 features.

---

**Note:** These rules reflect current C# 9 best practices as of 2025-06-26. Regularly review and update to maintain alignment with evolving standards.