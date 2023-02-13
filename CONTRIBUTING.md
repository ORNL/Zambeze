# Project Guidelines

Zambeze project progression is tracked on the GitHubs Zambeze project, all
tasks should be present in that project.  There are a total of 5 categories:

•	TODO – no one has started on this task
•	In Progress – someone has an open branch
•	Under Review – the branch is being reviewed
•	Merged with Devel
•	Merged with Main

# Maximizing the Team Throughput

Developers should be limited to working on one feature at a time, meaning they
should only have a single open PR that is either in the, “In progress”,
"Blocked" or “under review” categories.

## The Andon Cord

In assembly line manufacturing there is the concept of the Andon cord which is
pulled when a problem is discovered in the assembly line. A worker would then
pull the cord and the whole assembly line would stop and the resources of the
factory would all be made available to fixing the problem before everyone else
moved on their way.  Team priority should be shifted to anyone that is blocked
on a task. Members should feel comfortable pulling the proverbial Andon Cord.

## Pull Request Guidelines

1.	Branch Development
	a.	Feature branch
	b.	Nonfunctional/technical debt branch
2.	Merging from Devel to Main - release

## Branch Development

The following criteria should be satisfied.

1.	All new branches should be created from devel
2.	Any time a branch is created a pr should be immediately opened against the development branch.
3.	User who creates the PR is the primary contact – main responsible PR
4.	Branches should be merged with the development branch every day that new changes are made, this does not require the branch to have fully solved the solution it was created for but does require all ci automated tests to pass.
5.	In the face of failing automated tests, priority should be shifted to fixing the tests and merging before more work is done.
6.	Anyone who supplies a commit to a branch should use the GitHup PR Assignees option to indicate they are also working on the PR.
7.	Every PR should have at least one label assigned to it.
8.	All PRs should be part of the Zambeze Project
9.	All issues associated with the PR should be linked
10.	For work on a branch that is ongoing for several days, each day before committing a merge from devel back into the branch must be made.
11.	On successful merge of a branch the branch should be deleted

### Feature Branch Development

Feature branches should follow the naming scheme:
```
<GitHub_user_name>-<feature>
```
i.e.
```
JoshuaSBrown-transfer-activity
```

The username prepended to the branch name is to indicate who is responsible for
moving the branch forward in the development cycle and should serve as the
point of contact.

The following criteria should be satisfied.
1.	Unit tests should be added for all new features to prevent broken features down the road. If someone breaks a feature it is because there are not enough tests.
2.	All feature branches should have a milestone associated with them.

### Technical Debt or Nonfunctional branch

All non-feature branches should follow the naming scheme.
```
<GitHub_user_name>-<descriptive name>
```
i.e.
```
JoshuaSBrown-user-documentation
```

## Merging from Devel to Main – Release

An attempt to merge from devel into main should be made every week.
•	Merging from devel to main should be accompanied by a release iteration
•	Merging from devel to main requires all checks to pass:
o	Pyre type checking
o	Formatting
o	Unit and integration testing
•	Merging from devel to main requires all developers be added as reviewers
•	Requires at least one approval before merge can be completed
Labels
When a new issue or pull request is created a priority label should be added indicating how important the issue is.
Priority: Low - syntactic sugar, or addressing small amounts of technical debt or nonessential features
Priority: Medium - is important to the completion of a milestone but does not require immediate attention
Priority: High - is essential to the completion of a milestone
DevOps: CI – branch associated with 

# Zambeze Style Guide

* Code style guides should follow those of pep8 see link for details https://peps.python.org/pep-0008/
* Doc strings should follow those of the Sphinx style guide https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html
* In code comments can be made with '#'
