# Local hydraulic evidence inventory

Inventoried 2026-09-09 for CS-001. SHA-256 identifies the exact local evidence copy;
review status determines whether it may support the current computational basis.

## Primary research directory

| File | SHA-256 | Status and use |
| --- | --- | --- |
| `HDS-5.pdf` | `0444c21f401925bc1e7e5d57c11053b7311f903df9bb3c7d451f90a0d1770058` | Reviewed; April 2012 FHWA-HIF-12-026 final third edition; primary baseline |
| `TWRI_3-A3.pdf` | `ca76c71694117e45885159445e3e046967d664032d0e4da92ff7429f036d2c4e` | Reviewed; Bodhaine primary classification and historical examples |
| `FHWA-HRT-06-138.pdf` | `3af5b6c829d9e64da0599daa6341fb162d00892b9f4935861145bd5bfef0099a` | Reviewed; corrected electronic box-inlet report |
| `NCHRP-734.pdf` | `870e4e15af9aaf2070e05b4d3f2a2e24c3bb38785144e2cdde8b13652f9cfcd1` | Reviewed; primary research, with embedded-culvert data caveat below |
| `HY-8 User's Manual.pdf` | `267fef1f838945dcf7c0524ddd30c0b972e24abd3ace0eaec39d9aad8402a4f5` | Reviewed in applicable sections; v8.0 implementation documentation only |
| `AGRD05B-23_Guide_to_Road_Design_Part-5B_Drainage_Open_Channels_Culverts_and_Floodway_Crossings.pdf` | `76b40bf481d1d268e37343be216abea5707dffae6f7972467f9fa9343809f0cd` | Reviewed in applicable sections; Australian workflow and design context |
| `Reviewing Coefficients in Embedded Circular Culverts from NCHRP Report 734.pdf` | `3444a8cbae77aaf19410b4edf6674641e6307849308eac9628dde920b3a70d81` | Reviewed; HY-8 developer correction/extension, not primary method authority |
| `TFHRCReport.pdf` | `b2e89750e738fc0d47bbb32189e6f50d6ee3686f511ac824bf88fc150a8e9a7e` | Pending; FHWA-HRT-14-064 fish-passage scope is outside the initial solver |

## HY-8 bundled directory

| File | SHA-256 | Status and use |
| --- | --- | --- |
| `HY-8 User's Manual.pdf` | `267fef1f838945dcf7c0524ddd30c0b972e24abd3ace0eaec39d9aad8402a4f5` | Byte-identical duplicate of the reviewed `reference_docs/` copy |
| `Reviewing Coefficients in Embedded Circular Culverts from NCHRP Report 734.pdf` | `3444a8cbae77aaf19410b4edf6674641e6307849308eac9628dde920b3a70d81` | Byte-identical duplicate of the reviewed `reference_docs/` copy |
| `TFHRCReport.pdf` | `b2e89750e738fc0d47bbb32189e6f50d6ee3686f511ac824bf88fc150a8e9a7e` | Byte-identical duplicate; pending future fish-passage scope |
| `hds5.pdf` | `2e594fdbec982af88432536b51e9d3b40947faaac40bdb5f34fe44c381933459` | Rejected as baseline; January 2012 FHWA-NHI-12-029 copy differs from the final April publication above |
| `HY-8 7.6 Release Notes.pdf` | `5f3889db4f35a6ee82203bd34bad3d43372e57c49ee7b550b295a7552a9d3e9c` | Reviewed for version history and pointer to the embedded-coefficient correction; not 8.0.1.2 method authority |
| `HY-8 QuickTutorial.pdf` | `7ce23180d79f3e70d7f06c1176820c73c0a50b942ce7f6f55ecf53c9ac5d5e0b` | Rejected as technical authority; v7.6 user tutorial only |
| `hec14.pdf` | `7aea6892128ece86e15f69764c88863629b7423896ad954e6d4f0132188dbf9b` | Pending; energy-dissipator design is outside initial scope |
| `hec26.pdf` | `e0dfb11c0323d0a5f7dd784c74bf3a5b240e45f0c878a10cab4350cda5d648b9` | Pending; aquatic-organism passage is outside initial scope |

`ShapeDB.dat` is not a PDF but is pinned separately at SHA-256
`2479e9444feaff529313e18a1b26fc2de4f6b6c541db58477da6bebc602164a7`.
It is HY-8 implementation evidence, not a primary hydraulic publication.
