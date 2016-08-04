## 0.3 (2016-08-04)

- New: Add User model
- New: Add option for env vars for auth
- New: Add scope kwarg to Classification.where()
- New: Add SetMemberSubject class
- New: Submit subject links in batches in SubjectSet.add()
- New: oauth for client apps
- Fix: Skip trying to read export state if description was empty
- Fix: Don't rely on the response having a Content-Length header

## 0.2 (2016-07-21)

- New: Automatically retry failed image uploads
- New: Project classifications export
- New: Subject retirement in Workflow
- New: Add client ID for panoptes-staging.zooniverse.org
- New: Add ProjectPreferences
- New: Add Classification
- New: Removing subject set links
- Fix: IOError: Too many open files (in subject.py, line 64) #6

## 0.1 (2016-06-16)

- Initial release!
- Allows creating and modifying projects, subjects, subject sets
