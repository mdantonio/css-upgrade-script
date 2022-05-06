# CCS Upgrade Script

This is a naif script used to detect css classes that changed from Bootstrap 4 to Bootstrap 5 and from Font Awesome 5 to Font Awesome 6

Bootstrap 4 to 5 upgrade guide: https://ourtechroom.com/tech/bootstrap4-vs-boostrap5-migrate-differences/

Font Awesome 5 to 6 upgrade guide: https://fontawesome.com/docs/web/setup/upgrade/whats-changed#icons-renamed-in-version-6

## Usage

```
python3 scan.py --recursive /path/you/project/projects/project/frontend
```

Add `--fontawesome` flag to also include Font Awesome scan

```
python3 scan.py --recursive --fontawesome /path/you/project/projects/project/frontend
```

In case of false positives, you can skip specific css classes by using the `-i / --ignore` flag

```
python3 scan.py --recursive --fontawesome -i your-class1 -i your-class2 -i ... /path/you/project/projects/project/frontend
```
