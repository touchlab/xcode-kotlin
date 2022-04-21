package co.touchlab.xcode.cli.util

object BackupHelper {
    private val backupRoot = File(Path.home / ".xcode-kotlin" / "backup")

    fun backupPath(filename: String): Path {
        ensureBackupRootExists()
        return backupRoot.path / filename
    }

    fun ensureBackupRootExists() {
        if (!backupRoot.exists()) {
            backupRoot.mkdirs()
        }
    }

}