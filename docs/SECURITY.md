# Security and Licensed Software

- Never commit Junos credentials, tokens, private keys or `.env` files.
- Supply secrets through environment variables or ignored local files.
- Never redistribute licensed Juniper images, disks or derived artifacts.
- Keep passwords out of topology YAML and startup configurations.
- Sanitize runtime reports, packet captures, backups and core dumps before use.
- Review staged files and run a secret scanner before publication.

The repository contains orchestration code and documentation only. Users must
obtain and license Juniper software through authorized channels.
