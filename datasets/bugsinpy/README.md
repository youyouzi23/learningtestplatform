# BugsInPy adapter

The project uses the maintained
[BugsInPy repository](https://github.com/reproducing-research-projects/BugsInPy)
as a reproducible source of real Python defects. The dataset source code is not
vendored here. Follow its upstream setup instructions to check out and execute
the buggy (`-v 0`) and fixed (`-v 1`) revisions.

`sample_manifest.json` is a template, not evidence of an executed dataset case.
Bug 2 is used because it is the checkout example in the upstream README. Replace
the marked trigger test and failure log with output captured from an actual
BugsInPy run, then import it with:

```powershell
python scripts/import_bugsinpy.py `
  --manifest datasets/bugsinpy/sample_manifest.json `
  --task-id 1 `
  --api-key $env:API_ADMIN_KEY
```

The platform stores both outcomes, classifies the failure log, computes whether
the regression passed (`buggy` fails and `fixed` passes), and includes the
structured comparison in the task report.
