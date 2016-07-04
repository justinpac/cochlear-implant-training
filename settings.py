# Most settings are automatically handled by hipercore
# If you have any additional settings, you can add them here
# For example, your app may need to use a different database, or set some special environment variable

# Note: this may overwrite the default hipercore settings, so use with caution
# more info: http://hipercic-test.cs.stolaf.edu/doc/build-hipercic-apps.html#settings-py

MIDDLEWARE_CLASSES = ('apps.cochlear.middleware.PermissionsCheck',)

