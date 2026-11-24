# BIDS template collection for faire

Copier templates for the datasets of a neuroimaging study, versioned together. The `kind`
answer selects the template:

| `kind` | Dataset | Containers | bids-validator |
|---|---|---|---|
| `dicom-stream` | DICOM exports, one folder per session; instrument from the DICOM headers | none | none |
| `physio-stream` | physiological recordings, one folder per session | none | none |
| `eyetracking-stream` | eye-tracking EDF files, one folder per session | none | none |
| `mrs-stream` | raw MRS files, one folder per session | none | none |
| `ephys-stream` | MEG, EEG and iEEG recordings of any mix, one folder per session | none | none |
| `bids` | raw BIDS from DICOM (heudiconv), physio (phys2bids), eye-tracking (eye2bids), MRS (spec2nii) and MEG/EEG/iEEG (MNE-BIDS) streams, defaced | shared conversion collection (TODO) | blocking |
| `fmriprep` | fMRIPrep derivatives of `bids` | ReproNim | blocking |
| `smriprep` | sMRIPrep derivatives of `bids` | ReproNim | blocking |
| `qsiprep` | QSIPrep derivatives of `bids` | ReproNim | blocking |
| `qsirecon` | QSIRecon derivatives of `qsiprep` (and FreeSurfer of `smriprep`) | ReproNim | advisory |
| `bids-study` | the BIDS [study dataset](https://bids-specification.readthedocs.io/en/stable/common-principles.html#study-dataset) (`DatasetType: study`) | none | none |

All templates enable DataLad fake dates and process one session per pull request.

The study follows the BIDS study layout: raw BIDS at path `rawbids`, each derivative at
`derivatives/<dataset id>`. Derivatives' `SourceDatasets` assume that layout
(`../../rawbids/`, or `../<source>/` for derivatives of derivatives). Sourcedata streams
have no path in the superdataset; each derived dataset links them under its own
`sourcedata/`.

## Streams

`faire index <stream> <directory>` adds each top-level entry of the directory as one item,
using `.faire/heuristic.py` (static, `shared/heuristic.py`), configured by `.faire/heuristic.yml`, rendered
from these answers:

- `item_pattern`: regex on the item name; its named groups are the sample entities, plus
  optional `instrument` and `pilot`. Default: `sub-<subject>_ses-<session>[_pilot]`.
- `instrument_from`: `dicom` (default for `dicom-stream`; formats `dicom_instrument_format`,
  default `{ManufacturerModelName}{DeviceSerialNumber}`, needs `pydicom` where indexing
  runs), `name` (the `instrument` group), or `single` (default otherwise; the stream's only
  instrument).
- `place_format`: placement in the instance, default `sub-{subject}/ses-{session}`. The
  `bids` rules read `sourcedata/<stream>/*/sub-{subject}/ses-{session}/*`: change both
  together.

Instrument identifiers in the ma-DMP must be what the heuristic returns.

## Use from a ma-DMP

[`madmp.json`](madmp.json) is a starting ma-DMP for a whole study: DICOM, physio,
eye-tracking, raw MRS and electrophysiology streams, raw BIDS, the four derivatives and the study dataset, all from this
collection. Replace every
`TODO` and `example.org` value, and drop the streams and derivatives the study does not
have (with their answers and sources). Check it with `faire validate madmp.json`.

Pin every dataset of the study to the same tag and select its kind:

```json
"faire": {
  "template": {
    "repository": "https://example.org/faire-templates-bids",
    "version": "v0.1.0",
    "data": {"kind": "qsirecon", "runner": "gpu"}
  },
  "path": "derivatives/qsirecon"
}
```

Sources in the ma-DMP (`IsDerivedFrom`) must match the template answers: `source`, and for
`qsirecon` with a `*-hsvs` spec, `freesurfer_source`. The streams of `bids`
(`dicom_stream`, `physio_stream`, `eyetrack_stream`, `mrs_stream`, `ephys_stream`) must be its sources; leave the physio,
eye-tracking, MRS or electrophysiology stream empty to drop its rule.

## CI requirements

- Runners tagged with the `runner` answer (`TODO-runner` by default), with Apptainer.
- `FS_LICENSE`: GitLab CI variable of type *file* holding the FreeSurfer license.

## Before a first release

- `bids/.datalad/config`: URL and revision of the shared conversion collection, image paths
  of heudiconv, phys2bids, eye2bids, spec2nii, mne-bids, bids-validator and the defacing tool, and the defacing
  command.
- Default heuristics (`heuristic`, `phys2bids_heuristic`, `eye2bids_metadata`, `ephys_script`) in that
  collection.

Layout: `copier.yml` holds the questions of every kind; `shared/` holds the files several
templates use, linked from each template directory. Shared dotfiles are linked as
`.gitignore.jinja` and `.gitattributes.jinja`: git does not follow symlinked `.gitignore`
and `.gitattributes`, and the suffix keeps them from applying to this repository.
