from django.contrib.staticfiles.finders import AppDirectoriesFinder

from staticfiles import utils, storage

class LegacyAppDirectoriesFinder(AppDirectoriesFinder):
    """
    A legacy file finder that provides a migration path for the
    default directory name in previous versions of staticfiles, "media".
    """
    storage_class = storage.LegacyAppMediaStorage
