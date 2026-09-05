# Maven Dependency Conflict: Exclude Transitive slf4j-log4j12

### Context
In `pom.xml`, the dependency `com.example.legacy:legacy-connector` pulls in a transitive logging binding `org.slf4j:slf4j-log4j12`, creating a classpath conflict with modern `ch.qos.logback:logback-classic`.

### Objective
1. In `pom.xml`, add an `<exclusions>` element to the `legacy-connector` dependency.
2. Exclude group `org.slf4j` and artifact `slf4j-log4j12`.
3. Preserve both `legacy-connector` and `logback-classic` dependencies intact.

### Style
Standard Maven XML schema format with proper indentation.

### Tone
Precise, configuration and build-system oriented.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Update `pom.xml` with the appropriate exclusion declaration.
