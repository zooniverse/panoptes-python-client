## 1.2 (2020-06-13)

- New: Add `SubjectWorkflowStatus` class
- New: Add attached image methods to `Project`
- Fix: Save workflow configuration if changed
- Change: Update requests requirement >=2.4.2,<2.25
- Change: Update mock requirement to >=2.0,<4.1
- Change: Update future requirement from to >=0.16,<0.19

## 1.1.1 (2019-02-25)

- Fix: Can't save new objects with individual links
- Fix: Missing 'six' dependency

## 1.1 (2019-02-08)

- New: Add asynchronous multi-threaded subject creation
- New: Add `LinkCollection` for managing links to multiple objects
- New: Allow `Panoptes` class to act as a context manager
- New: Add `Panoptes.interactive_login` method
- New: Add authentication method selection (via `Panoptes.connect(login=...)`)
- New: Add `CollectionRole` class
- New: Add `Collection.set_default_subject()`
- New: Add `SubjectSet.__contains__()`
- New: Add `PanoptesObject.delete()` method
- New: Add `Organization` class
- New: Add `Project.avatar`
- New: Allow finding `Collection`s by slug
- New: Allow finding `User`s from a list of email addresses
- New: Allow batched `User` lookups by login name
- New: Allow editing `Collection` project links and descriptions
- New: Allow editing `Workflow` `tasks`, `primary_language`, and `mobile_friendly`
- New: Allow editing `User.valid_user`

- Fix: Fix reloading for `User` class
- Fix: Passing `set`s to batchable methods

- Change: Use multiple threads for media uploads
- Change: Make global client thread safe
- Change: Retry all `GET` requests on server failures
- Change: Log in immediately rather than waiting for first request
- Change: Raise an exception if media mime type can't be determined
- Change: Log a warning if libmagic is broken
- Change: Use six for string type checking
- Change: Raise exception when linking unsaved objects
- Change: Update requests requirement to >=2.4.2,<2.22
- Change: Update future requirement to >=0.16,<0.18

## 1.0.3 (2018-07-30)

- Fix: TypeError when creating subjects
- Update default client IDs

## 1.0.2 (2018-07-25)

- Fix: Fix saving subjects with updated metadata
- Fix: Fix calling `Subject.save()` when nothing has changed

## 1.0.1 (2018-06-14)

- Fix: Exports are not automatically decompressed on download
- Fix: Unable to `save` a Workflow
- Fix: Fix typo in documentation for Classification
- Fix: Fix saving objects initialised from object links

## 1.0 (2017-11-03)

- New: Add methods for adding Project links
- New: Enable debugging if PANOPTES_DEBUG is set in env
- Fix: Fix accessing list of linked projects
- Move testing dependencies to extras
- Change User.avatar to be a property
- Specify dependency versions

## 0.10 (2017-08-04)

- Fix: Avoid reloading resource after create actions
- Fix: Add buffer to bearer token expiration check
- Remove default export timeout

## 0.9 (2017-06-20)

- New: Add support for non-image media types (requires libmagic)
- New: Allow lazy loading of objects
- New: Add `WorkflowVersion` class and `Workflow.versions` property
- Fix: Don't submit empty JSON by default for GET requests
- Fix: Adding location paths in Python 2
- Fix: Return a list of linked objects instead of a map in Python 3
- Use `SetMemberSubject` for `SubjectSet.subjects` lookup to improve speed
- Set default endpoint to www.zooniverse.org
- Raise TypeError if positional batchable argument is missing
- Convert `Collection.subjects` and `SubjectSet.subjects` to properties

## 0.8 (2017-05-11)

- New: Python 3 compatibility
- Fix: Fix passing sets to batchable methods
- Fix: `AttributeError` in `Workflow.add_subject_sets()`

## 0.7 (2017-03-22)

- New: Add Collection
- New: Allow editing of workflows
- New: Add method to get User's avatar
- New: Add support for iterating over numpy arrays
- New: Add per-Workflow exports
- Fix: setting endpoint in environment variable
- Fix: Stop iterating if there are no objects in the current page

## 0.6 (2017-01-11)

- New: Add Project.collaborators() and ProjectRole
- New: Add admin option
- Fix: Raise PanoptesAPIException instead of StopIteration
- Fix: Make ResultPaginator handle None responses
- Fix: Raise PanoptesAPIException instead of StopIteration in PanoptesObject.where()

## 0.5 (2016-11-21)

- New: Send SubjectSet.remove() requests in batches
- Fix: Raise PanoptesAPIException instead of StopIteration in Project.find()
- Fix: Don't read the image file on every upload attempt

## 0.4.1 (2016-09-21)

- Fix: Bearer token checking only occurs when necessary

## 0.4 (2016-09-02)

- New: Support for all data exports
- New: Project owners can update `ProjectPreference` settings
- New: Removed `subject_sets` method and `SetMemberSubject` (now in links)
- New: Add set to iterable types
- Fix: Only save links if it's been modified
- Fix: Specify minimum requests version

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
