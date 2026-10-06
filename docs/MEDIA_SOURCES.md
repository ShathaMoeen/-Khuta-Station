# KHUTA media sources and rights audit

KHUTA currently has an additive `app.media_assets` registry. The visitor API selects media only when both `verification_status = 'verified'` and `rights_status = 'permitted'`. No media rows are registered in PostgreSQL, so no station image is returned to the demo screen.

| Station | Title | Institution | Source URL | License | License URL | Attribution | Verification | Rights |
|---|---|---|---|---|---|---|---|---|
| Unassigned | `photo_5913747965040332825_y.jpg` (unregistered file at `khutta/photo_5913747965040332825_y.jpg`) | Unknown | Unknown | Unknown | Unknown | Unknown | unverified | needs_review |

The file has no station association or source/rights metadata in the current project. It is not displayed. No images of prophets or other sensitive religious figures were added. No external images were downloaded. Add a row only after the source, license, attribution and station association have been checked and recorded; do not mark it permitted based on appearance or availability.
