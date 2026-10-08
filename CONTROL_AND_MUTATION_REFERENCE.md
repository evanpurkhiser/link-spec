# Link Export control and mutation commands

This generated reference joins Rekordbox 7.2.19 server dispatch with the
pinned XDJ-RR client call graph for every `0x2x05` write, `0x2x07` database
modification, and `0x3xxx` control/state request. It complements the menu
query graph by documenting commands that mutate state, read scalar state,
write analysis data, or are recognized and rejected outside list browsing.

The domain contains 54 commands. XDJ-RR has direct
callers for 30 commands across
97 call sites.

## Command map

| Kind | Name | Effect | Rekordbox dispatcher | Target | Reply | XDJ-RR callers | Locations |
| ---: | --- | --- | --- | --- | ---: | ---: | --- |
| `2005` | `CMD_SAV_WAVE` | mutation-or-state-write | PSvDBMain::OnWriteCmd | PSvDBMain::SavWave | - | 2 | 8 |
| `2105` | `CMD_SAV_USB_CUE` | mutation-or-state-write | PSvDBMain::OnWriteCmd | PSvDBMain::SavUsbCue | 4702 | 2 | 8 |
| `2107` | `CMD_MOD_TRACK_RATE` | mutation-or-state-write | PSvDBMain::OnDbModCmd | PSvAppSyncDBIF::modTrackRate via database-interface vtable +0x2A0 | 4000 | 1 | 1 |
| `2205` | `CMD_SAV_VBR_INFO` | recognized-static-route | PSvDBMain::OnWriteCmd | PSvDBMain::SavVbrInf (constant-success stub) | - | 1 | 8 |
| `2207` | `CMD_CHG_KUVO_STATUS` | rejected | PSvDBMain::OnDbModCmd | - | 4003 | 0 | - |
| `2305` | `CMD_SAV_DISC_CUE` | recognized-log-only | PSvDBMain::OnWriteCmd | recognized-log-only | - | 2 | 8 |
| `2405` | `CMD_DEL_ALL_DISC_CUE` | recognized-log-only | PSvDBMain::OnWriteCmd | recognized-log-only | - | 2 | 8 |
| `2505` | `CMD_REG_DISCID` | recognized-log-only | PSvDBMain::OnWriteCmd | recognized-log-only | - | 1 | 8 |
| `2507` | `REKORDBOX_STATIC_PSVAPPSYNCDBIF::MODTRACKBPM VIA DATABASE_INTERFACE VTABLE +0X2A8` | mutation-or-state-write | PSvDBMain::OnDbModCmd | PSvAppSyncDBIF::modTrackBPM via database-interface vtable +0x2A8 | 4000 | 0 | - |
| `2605` | `CMD_SAV_QTZ_OFFSET` | mutation-or-state-write | PSvDBMain::OnWriteCmd | PSvDBMain::SavQtzOfs | 4000 | 1 | 1 |
| `2705` | `CMD_SAV_USB_CUE2` | mutation-or-state-write | PSvDBMain::OnWriteCmd | PSvDBMain::SavUsbCueExt | 4E02 | 1 | 8 |
| `2805` | `CMD_SAV_SPECIFIED_ATOM_INFO` | mutation-or-state-write | PSvDBMain::OnWriteCmd | PSvDBMain::SaveSpecifiedAtomInfo | 4000 | 0 | - |
| `2905` | `CMD_UPD_SPECIFIED_ATOM_INFO` | mutation-or-state-write | PSvDBMain::OnWriteCmd | PSvDBMain::UpdateSpecifiedAtomInfo | 4000 | 0 | - |
| `3000` | `CMD_LEFT_BUF` | list-buffer-render | PSvDBMain::OnListBuffCmd | PSvDBMain::GetListBufContents | 4001/4101/4201 | 27 | 1, 2, 3, 4, 5, 6, 7, 8 + dynamic |
| `3001` | `CMD_INSERT_HISTORY` | mutation-or-state-write | PSvDBMain::OnHistoryCmd | insert-history | - | 3 | 8 |
| `3002` | `CMD_ADD_PREPARE` | mutation-or-state-write | PSvDBMain::OnPrepareCmd | add-prepare | - | 4 | 8 |
| `3003` | `CMD_COLOR_CODE` | recognized-static-route | PSvDBMain::OnOtherCmd | color-code | - | 0 | - |
| `3005` | `CMD_CHK_NEWCMD_ENBL` | rejected | PSvDBMain::OnOtherClientCmd | - | 4003 | 0 | - |
| `3006` | `CMD_GET_USER_INFO` | state-query | PSvDBMain::OnUserCmd | PSvDBMain::GetDJID | 4D02 | 0 | - |
| `3007` | `CMD_SET_FILTER_ONOFF` | mutation-or-state-write | PSvDBMain::OnFilterCmd | set-filter-onoff | - | 0 | - |
| `3008` | `CMD_GET_BPM` | state-query | PSvDBMain::OnOther2Cmd | database-interface vtable +0x228 | 4000 | 0 | - |
| `3100` | `CMD_GET_OFFSET_CONTENTID` | state-query | PSvDBMain::OnListBuffCmd | PSvDBMain::GetListBufOffset | 4000 | 26 | 1, 3, 4, 6, 7 |
| `3101` | `CMD_DEL_HISTORY` | mutation-or-state-write | PSvDBMain::OnHistoryCmd | delete-history | - | 1 | 8 |
| `3102` | `CMD_ADD_TAGLIST_PLAYLIST` | mutation-or-state-write | PSvDBMain::OnPrepareCmd | add-taglist-playlist | - | 1 | 6 |
| `3103` | `REKORDBOX_STATIC_UNLISTED_STATIC_ARM` | recognized-static-route | PSvDBMain::OnOtherCmd | unlisted-static-arm | - | 0 | - |
| `3104` | `CMD_DEL_PLAYLIST` | recognized-static-route | PSvDBMain::OnOtherClientCmd | recognized zero-result special case | 4000 | 1 | 8 |
| `3107` | `CMD_GET_FILTER_CONDITION_PROPERTY` | state-query | PSvDBMain::OnFilterCmd | get-filter-condition-property | - | 0 | - |
| `3201` | `CMD_SET_ONAIR` | mutation-or-state-write | PSvDBMain::OnHistoryCmd | set-onair | - | 1 | 8 |
| `3202` | `REKORDBOX_STATIC_UNLISTED_STATIC_ARM` | recognized-static-route | PSvDBMain::OnPrepareCmd | unlisted-static-arm | - | 1 | 6 |
| `3203` | `CMD_GET_DB_FIRM_VER` | state-query | PSvDBMain::OnOtherCmd | get-db-firmware-version | - | 0 | - |
| `3207` | `CMD_SET_FILTER_CONDITION_PROPERTY` | mutation-or-state-write | PSvDBMain::OnFilterCmd | set-filter-condition-property | - | 0 | - |
| `3301` | `CMD_DEL_HISTORY_REPLY` | recognized-static-route | PSvDBMain::OnHistoryCmd | delete-history-reply | - | 0 | - |
| `3302` | `CMD_CHG_TAGLIST_ORDER` | mutation-or-state-write | PSvDBMain::OnPrepareCmd | change-taglist-order | - | 0 | - |
| `3303` | `CMD_GET_BRWS_TYPE` | state-query | PSvDBMain::OnOtherCmd | get-browse-type | - | 5 | 2 |
| `3307` | `CMD_SET_FILTER_CONDITION_MYTAG` | mutation-or-state-write | PSvDBMain::OnFilterCmd | set-filter-condition-mytag | - | 0 | - |
| `3401` | `CMD_DEL_HISTORY_TRACK` | mutation-or-state-write | PSvDBMain::OnHistoryCmd | delete-history-track | - | 1 | 1 |
| `3402` | `CMD_IS_TAGLIST_PLAYLIST` | state-query | PSvDBMain::OnPrepareCmd | is-taglist-playlist | - | 1 | 6 |
| `3403` | `REKORDBOX_STATIC_UNLISTED_STATIC_ARM` | recognized-static-route | PSvDBMain::OnOtherCmd | unlisted-static-arm | - | 0 | - |
| `3407` | `CMD_ADD_FILTER_MYTAG_ITEM` | mutation-or-state-write | PSvDBMain::OnFilterCmd | add-filter-mytag-item | - | 0 | - |
| `3501` | `CMD_GET_CURRENT_HISTORY_ID` | rejected | PSvDBMain::OnHistoryCmd | - | 4003 | 0 | - |
| `3503` | `CMD_INFO_UNPLAYABLE` | recognized-static-route | PSvDBMain::OnOtherCmd | info-unplayable | - | 1 | 8 |
| `3602` | `CMD_REPLACE_TAGLIST` | rejected | PSvDBMain::OnPrepareCmd | - | 4003 | 0 | - |
| `3603` | `CMD_GET_DB_HIERARCHY` | state-query | PSvDBMain::OnOtherCmd | get-db-hierarchy | - | 2 | 7 |
| `3703` | `REKORDBOX_STATIC_UNLISTED_STATIC_ARM` | recognized-static-route | PSvDBMain::OnOtherCmd | unlisted-static-arm | - | 0 | - |
| `3704` | `CMD_APPEND_PLAYLIST` | rejected | special-0x3104-only | - | 4003 | 0 | - |
| `3803` | `REKORDBOX_STATIC_UNLISTED_STATIC_ARM` | recognized-static-route | PSvDBMain::OnOtherCmd | unlisted-static-arm | - | 0 | - |
| `3804` | `CMD_REPLACE_PLAYLIST_TRACK` | rejected | special-0x3104-only | - | 4003 | 0 | - |
| `3903` | `CMD_PROPERTY_TABLE` | state-query | PSvDBMain::OnOtherCmd | property-table | - | 2 | 8 |
| `3A03` | `CMD_TRANS_NEWKEY` | state-query | PSvDBMain::OnOtherCmd | translate-new-key | - | 1 | 1 |
| `3B03` | `CMD_GET_PLAYSTATE` | state-query | PSvDBMain::OnOtherCmd | get-play-state | - | 1 | 1 |
| `3C03` | `CMD_SET_MY_SETTING_FLG` | mutation-or-state-write | PSvDBMain::OnOtherCmd | set-my-setting-flag | - | 1 | 1 |
| `3D03` | `CMD_GET_NEW_KEY_ID` | state-query | PSvDBMain::OnOtherCmd | get-new-key-id | - | 1 | 1 |
| `3E03` | `CMD_GET_IS_RBM_MOUNT` | rejected | PSvDBMain::OnOtherCmd | - | 4003 | 1 | 1 |
| `3F03` | `CMD_SET_BACKGROUND_COLOR` | rejected | PSvDBMain::OnOtherCmd | - | 4003 | 2 | 1 |

## Command details

### `2005` `CMD_SAV_WAVE`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::SavWave.
- Target: PSvDBMain::SavWave; reply: -.
- Database: djmdContent.AnalysisDataPath. Filesystem/effect: SavWave resolves the analysis path and writes 400 loud-wave samples plus 100 dot-wave bytes through MstStoreLoudWave and MstStoreDotWave.
- XDJ-RR: 2 direct call sites; wrappers dbcl_RegDiscWave, dbcl_RegSdUsbWave; callers ReqRegistWave; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:10802` `ReqRegistWave` -> `dbcl_RegDiscWave` at `0x001ffc0c`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:10812` `ReqRegistWave` -> `dbcl_RegSdUsbWave` at `0x001ffc0c`, location `8` (wrapper-fixed).

### `2105` `CMD_SAV_USB_CUE`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::SavUsbCue.
- Target: PSvDBMain::SavUsbCue; reply: 4702.
- Database: djmdCue and cue-option rows. Filesystem/effect: No audio decoding is visible; the legacy cue writer mutates cue records and returns the resulting 4702 cue set.
- XDJ-RR: 2 direct call sites; wrappers dbcl_DelUsbSdCue, dbcl_RegUdbSdCue; callers DbDeleteUsbSdCue, DbRegistUsbSdCue; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:6728` `DbRegistUsbSdCue` -> `dbcl_RegUdbSdCue` at `0x001f9e6c`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:6917` `DbDeleteUsbSdCue` -> `dbcl_DelUsbSdCue` at `0x001fa1e8`, location `8` (wrapper-fixed).

### `2107` `CMD_MOD_TRACK_RATE`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnDbModCmd, PSvAppSyncDBIF::modTrackRate via database-interface vtable +0x2A0.
- Target: PSvAppSyncDBIF::modTrackRate via database-interface vtable +0x2A0; reply: 4000.
- Database: djmdContent.Rating. Filesystem/effect: No filesystem access is visible; modTrackRate reads the current Rating and updates it by content ID only when the byte value changes.
- XDJ-RR: 1 direct call sites; wrappers dbcl_SetRateValue2Track; callers SetRateValue2Track; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:12545` `SetRateValue2Track` -> `dbcl_SetRateValue2Track` at `0x0020f34c`, location `1` (wrapper-fixed).

### `2205` `CMD_SAV_VBR_INFO`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::SavVbrInf (constant-success stub).
- Target: PSvDBMain::SavVbrInf (constant-success stub); reply: -.
- Database: -. Filesystem/effect: SavVbrInf is a constant-success stub in Rekordbox 7.2.19 and does not inspect its message.
- XDJ-RR: 1 direct call sites; wrappers dbcl_RegVBRInfo; callers RegVbrInfo; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7183` `RegVbrInfo` -> `dbcl_RegVBRInfo` at `0x001fa7bc`, location `8` (wrapper-fixed).

### `2207` `CMD_CHG_KUVO_STATUS`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnDbModCmd, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: PSvDBMain::OnDbModCmd recognizes only 2107, 2507.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `2305` `CMD_SAV_DISC_CUE`

- Classification: `recognized-log-only`; coverage `rekordbox-recognized-log-only`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, recognized-log-only.
- Target: recognized-log-only; reply: -.
- Database: -. Filesystem/effect: Rekordbox recognizes and logs this disc-cue write kind but invokes no writer and sends no reply.
- XDJ-RR: 2 direct call sites; wrappers dbcl_DelDiscCue, dbcl_RegDiscCue; callers DbDeleteDiscCue, DbRegistDiscCue; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:6850` `DbRegistDiscCue` -> `dbcl_RegDiscCue` at `0x001fa0b4`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:6990` `DbDeleteDiscCue` -> `dbcl_DelDiscCue` at `0x001fa33c`, location `8` (wrapper-fixed).

### `2405` `CMD_DEL_ALL_DISC_CUE`

- Classification: `recognized-log-only`; coverage `rekordbox-recognized-log-only`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, recognized-log-only.
- Target: recognized-log-only; reply: -.
- Database: -. Filesystem/effect: Rekordbox recognizes and logs this delete-all-disc-cue kind but invokes no writer and sends no reply.
- XDJ-RR: 2 direct call sites; wrappers dbcl_DelAllCue, dbcl_DelAllCueOfAllDisc; callers DbDeleteAllDiscCue, DbDeleteDiscAllCue; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7031` `DbDeleteDiscAllCue` -> `dbcl_DelAllCue` at `0x001fa470`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7062` `DbDeleteAllDiscCue` -> `dbcl_DelAllCueOfAllDisc` at `0x001fa540`, location `8` (wrapper-fixed).

### `2505` `CMD_REG_DISCID`

- Classification: `recognized-log-only`; coverage `rekordbox-recognized-log-only`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, recognized-log-only.
- Target: recognized-log-only; reply: -.
- Database: -. Filesystem/effect: Rekordbox recognizes and logs this disc-ID registration kind but invokes no writer and sends no reply.
- XDJ-RR: 1 direct call sites; wrappers dbcl_ReqRegDiscID; callers ReqRegistDiscID; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7141` `ReqRegistDiscID` -> `dbcl_ReqRegDiscID` at `0x001fa6a0`, location `8` (wrapper-fixed).

### `2507` `REKORDBOX_STATIC_PSVAPPSYNCDBIF::MODTRACKBPM VIA DATABASE_INTERFACE VTABLE +0X2A8`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnDbModCmd, PSvAppSyncDBIF::modTrackBPM via database-interface vtable +0x2A8.
- Target: PSvAppSyncDBIF::modTrackBPM via database-interface vtable +0x2A8; reply: 4000.
- Database: djmdContent.BPM. Filesystem/effect: No filesystem access is visible; modTrackBPM reads the current BPM and updates it by content ID only when the value changes.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `2605` `CMD_SAV_QTZ_OFFSET`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::SavQtzOfs.
- Target: PSvDBMain::SavQtzOfs; reply: 4000.
- Database: djmdContent.AnalysisDataPath, djmdContent.ContentLink. Filesystem/effect: SavQtzOfs writes the quantize offset to the analysis path, then mirrors its nonzero state into ContentLink bit zero.
- XDJ-RR: 1 direct call sites; wrappers dbcl_RegQtzOfsInfo; callers RegQtzOfsInfo; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7280` `RegQtzOfsInfo` -> `dbcl_RegQtzOfsInfo` at `0x001fa970`, location `1` (wrapper-fixed).

### `2705` `CMD_SAV_USB_CUE2`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::SavUsbCueExt.
- Target: PSvDBMain::SavUsbCueExt; reply: 4E02.
- Database: djmdCue and cue-option rows. Filesystem/effect: No audio decoding is visible; SavUsbCueExt applies the extended cue mutation and replies through RetNewCueToClient (4E02).
- XDJ-RR: 1 direct call sites; wrappers dbcl_SaveUdbSdCue_Ext; callers DbUpdateUsbSdCue_Ext; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7632` `DbUpdateUsbSdCue_Ext` -> `dbcl_SaveUdbSdCue_Ext` at `0x001fab68`, location `8` (wrapper-fixed).

### `2805` `CMD_SAV_SPECIFIED_ATOM_INFO`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::SaveSpecifiedAtomInfo.
- Target: PSvDBMain::SaveSpecifiedAtomInfo; reply: 4000.
- Database: djmdContent.AnalysisDataPath. Filesystem/effect: SaveSpecifiedAtomInfo validates the atom and extension, derives a sibling analysis file, and writes it through MstSaveAtomData.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `2905` `CMD_UPD_SPECIFIED_ATOM_INFO`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnMAnlzClientCmd, PSvDBMain::OnWriteCmd, PSvDBMain::UpdateSpecifiedAtomInfo.
- Target: PSvDBMain::UpdateSpecifiedAtomInfo; reply: 4000.
- Database: djmdContent.AnalysisDataPath. Filesystem/effect: UpdateSpecifiedAtomInfo accepts PQT2 only, derives a sibling analysis file, and updates it through MstUpdateAtomData.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3000` `CMD_LEFT_BUF`

- Classification: `list-buffer-render`; coverage `real-rekordbox-menu-oracle`; evidence ALPHA, OBS, DB, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnListBuffCmd, PSvDBMain::GetListBufContents.
- Target: PSvDBMain::GetListBufContents; reply: 4001/4101/4201.
- XDJ-RR: 27 direct call sites; wrappers dbcl_GetLeftBuf; callers AddPrepare, DbReqCueBankDragDrop, GetAllPrepRecFromDB, GetAllRecFromDB, GetCdda_1stMusicID, GetCdrom_1stMusicID, GetFileAttr, GetFileAttr.constprop.0, GetLeftInfomationRec, GetLeftInfomationRec.constprop.8, GetLeftPrepareJump, GetListAfterJump2Char, GetLoadedMusicData, GetMusicIDRenew, GetOffsetInCate, GetOneData_SongInfo, GetRightBrowseOneData, GetRightPrepareList, GetRootCateItems, GetSortMenuList, GetTrack2MusicID, InfoJumpSetDepth0, ReloadCateBrws, ReloadCatePac, SetLoadSearchDepth0; literal locations 1, 2, 3, 4, 5, 6, 7, 8; dynamic location also used.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:6363` `GetRootCateItems` -> `dbcl_GetLeftBuf` at `0x001690e4`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:7679` `GetAllPrepRecFromDB` -> `dbcl_GetLeftBuf` at `0x0016aea0`, location `6` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8115` `GetLeftPrepareJump` -> `dbcl_GetLeftBuf` at `0x0016b914`, location `6` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8811` `GetRightPrepareList` -> `dbcl_GetLeftBuf` at `0x0016c948`, location `2` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:9009` `AddPrepare` -> `dbcl_GetLeftBuf` at `0x0016d05c`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:9065` `AddPrepare` -> `dbcl_GetLeftBuf` at `0x0016d05c`, location `6` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0017.c:2601` `GetAllRecFromDB` -> `dbcl_GetLeftBuf` at `0x00173ee0`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0017.c:2917` `GetListAfterJump2Char` -> `dbcl_GetLeftBuf` at `0x00174728`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0017.c:7552` `GetRightBrowseOneData` -> `dbcl_GetLeftBuf` at `0x0017ab24`, location `2` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:6521` `DbReqCueBankDragDrop` -> `dbcl_GetLeftBuf` at `0x001f9a14`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:8918` `GetSortMenuList` -> `dbcl_GetLeftBuf` at `0x001fcc5c`, location `5` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10142` `GetOffsetInCate` -> `dbcl_GetLeftBuf` at `0x0020b674`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10604` `InfoJumpSetDepth0` -> `dbcl_GetLeftBuf` at `0x0020c024`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:11266` `GetLeftInfomationRec.constprop.8` -> `dbcl_GetLeftBuf` at `0x0020d368`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:12046` `GetLeftInfomationRec` -> `dbcl_GetLeftBuf` at `0x0020e6d0`, location `param_3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:12655` `GetOneData_SongInfo` -> `dbcl_GetLeftBuf` at `0x0020f3d4`, location `5` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:492` `SetLoadSearchDepth0` -> `dbcl_GetLeftBuf` at `0x00210a54`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:621` `GetCdda_1stMusicID` -> `dbcl_GetLeftBuf` at `0x00210cd0`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:769` `GetCdrom_1stMusicID` -> `dbcl_GetLeftBuf` at `0x00211008`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:1264` `GetLoadedMusicData` -> `dbcl_GetLeftBuf` at `0x002116e4`, location `4` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:1267` `GetLoadedMusicData` -> `dbcl_GetLeftBuf` at `0x002116e4`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:1699` `GetFileAttr.constprop.0` -> `dbcl_GetLeftBuf` at `0x002127bc`, location `8` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:1812` `GetFileAttr` -> `dbcl_GetLeftBuf` at `0x00212b38`, location `8` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:2840` `GetTrack2MusicID` -> `dbcl_GetLeftBuf` at `0x00214148`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3021` `GetMusicIDRenew` -> `dbcl_GetLeftBuf` at `0x00214544`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3292` `ReloadCateBrws` -> `dbcl_GetLeftBuf` at `0x00214c8c`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3473` `ReloadCatePac` -> `dbcl_GetLeftBuf` at `0x00215228`, location `7` (call-argument-2).

### `3001` `CMD_INSERT_HISTORY`

- Classification: `mutation-or-state-write`; coverage `real-rekordbox-menu-oracle`; evidence ALPHA, OBS, DB, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnHistoryCmd, insert-history.
- Target: insert-history; reply: -.
- XDJ-RR: 3 direct call sites; wrappers dbcl_InsertSong2History; callers ReqAddHistory, ReqAddPlayHistory, SelectRightMenu; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:10308` `SelectRightMenu` -> `dbcl_InsertSong2History` at `0x001fe73c`, location `8` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:2473` `ReqAddHistory` -> `dbcl_InsertSong2History` at `0x00213ab0`, location `8` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3107` `ReqAddPlayHistory` -> `dbcl_InsertSong2History` at `0x00214b04`, location `8` (call-argument-2).

### `3002` `CMD_ADD_PREPARE`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnPrepareCmd, add-prepare.
- Target: add-prepare; reply: -.
- XDJ-RR: 4 direct call sites; wrappers dbcl_AddPrepare; callers AddPrepare; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8995` `AddPrepare` -> `dbcl_AddPrepare` at `0x0016d05c`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:9029` `AddPrepare` -> `dbcl_AddPrepare` at `0x0016d05c`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:9055` `AddPrepare` -> `dbcl_AddPrepare` at `0x0016d05c`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:9074` `AddPrepare` -> `dbcl_AddPrepare` at `0x0016d05c`, location `8` (wrapper-fixed).

### `3003` `CMD_COLOR_CODE`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, color-code.
- Target: color-code; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3005` `CMD_CHK_NEWCMD_ENBL`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, unsupported-low-byte, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: other-client-low-byte routes low byte 0x05 to unsupported-low-byte.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3006` `CMD_GET_USER_INFO`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnUserCmd, PSvDBMain::GetDJID.
- Target: PSvDBMain::GetDJID; reply: 4D02.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3007` `CMD_SET_FILTER_ONOFF`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnFilterCmd, set-filter-onoff.
- Target: set-filter-onoff; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3008` `CMD_GET_BPM`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOther2Cmd, database-interface vtable +0x228.
- Target: database-interface vtable +0x228; reply: 4000.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3100` `CMD_GET_OFFSET_CONTENTID`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnListBuffCmd, PSvDBMain::GetListBufOffset.
- Target: PSvDBMain::GetListBufOffset; reply: 4000.
- XDJ-RR: 26 direct call sites; wrappers dbcl_GetOffsetCID, dbcl_GetOffsetCID2; callers ExecInfoJumpBrwsLocal, ExecInfoJumpPrepare, ExecInformationJump, GetCdda_1stMusicID, GetCdrom_1stMusicID, GetFileAttrMusicID, GetFileAttrMusicID2, GetListFromDBWithLastPos, GetListOfPlaying, GetLoadedMusicData, GetMusicIDRenew, InfoJumpSetDepth0, ReLoadIfLoadInPreare, SelectRightMenu, SendSortedBrwsList, SetLoadSearchDepth0; literal locations 1, 3, 4, 6, 7.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8942` `ReLoadIfLoadInPreare` -> `dbcl_GetOffsetCID2` at `0x0016cf80`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0017.c:2803` `GetListFromDBWithLastPos` -> `dbcl_GetOffsetCID2` at `0x00174530`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0019.c:8553` `GetListOfPlaying` -> `dbcl_GetOffsetCID2` at `0x0019b7fc`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0019.c:8639` `GetListOfPlaying` -> `dbcl_GetOffsetCID2` at `0x0019b7fc`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0019.c:8751` `GetListOfPlaying` -> `dbcl_GetOffsetCID2` at `0x0019b7fc`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0019.c:8905` `GetListOfPlaying` -> `dbcl_GetOffsetCID2` at `0x0019b7fc`, location `4` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0019.c:8957` `GetListOfPlaying` -> `dbcl_GetOffsetCID2` at `0x0019b7fc`, location `4` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:8189` `SendSortedBrwsList` -> `dbcl_GetOffsetCID` at `0x001fb8d4`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:10465` `SelectRightMenu` -> `dbcl_GetOffsetCID2` at `0x001fe73c`, location `6` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10280` `ExecInfoJumpPrepare` -> `dbcl_GetOffsetCID2` at `0x0020b810`, location `6` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10582` `InfoJumpSetDepth0` -> `dbcl_GetOffsetCID` at `0x0020c024`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10750` `ExecInfoJumpBrwsLocal` -> `dbcl_GetOffsetCID2` at `0x0020c1b8`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10950` `ExecInformationJump` -> `dbcl_GetOffsetCID2` at `0x0020c60c`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:11193` `ExecInformationJump` -> `dbcl_GetOffsetCID2` at `0x0020c60c`, location `1` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:462` `SetLoadSearchDepth0` -> `dbcl_GetOffsetCID` at `0x00210a54`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:465` `SetLoadSearchDepth0` -> `dbcl_GetOffsetCID` at `0x00210a54`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:475` `SetLoadSearchDepth0` -> `dbcl_GetOffsetCID` at `0x00210a54`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:612` `GetCdda_1stMusicID` -> `dbcl_GetOffsetCID` at `0x00210cd0`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:827` `GetCdrom_1stMusicID` -> `dbcl_GetOffsetCID` at `0x00211008`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:1308` `GetLoadedMusicData` -> `dbcl_GetOffsetCID` at `0x002116e4`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:1966` `GetFileAttrMusicID` -> `dbcl_GetOffsetCID` at `0x00212ec8`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:2609` `GetFileAttrMusicID2` -> `dbcl_GetOffsetCID2` at `0x00213d3c`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:2635` `GetFileAttrMusicID2` -> `dbcl_GetOffsetCID2` at `0x00213d3c`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:2993` `GetMusicIDRenew` -> `dbcl_GetOffsetCID2` at `0x00214544`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3001` `GetMusicIDRenew` -> `dbcl_GetOffsetCID2` at `0x00214544`, location `3` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3063` `GetMusicIDRenew` -> `dbcl_GetOffsetCID2` at `0x00214544`, location `3` (call-argument-2).

### `3101` `CMD_DEL_HISTORY`

- Classification: `mutation-or-state-write`; coverage `real-rekordbox-menu-oracle`; evidence ALPHA, OBS, DB, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnHistoryCmd, delete-history.
- Target: delete-history; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_DelHistory; callers DBC_ReqDelHistory; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:9765` `DBC_ReqDelHistory` -> `dbcl_DelHistory` at `0x001fe16c`, location `8` (call-argument-2).

### `3102` `CMD_ADD_TAGLIST_PLAYLIST`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnPrepareCmd, add-taglist-playlist.
- Target: add-taglist-playlist; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_AddTaglist2Playlist; callers DbReqTaglist2Playlist; literal locations 6.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:4049` `DbReqTaglist2Playlist` -> `dbcl_AddTaglist2Playlist` at `0x002161a4`, location `6` (wrapper-fixed).

### `3103` `REKORDBOX_STATIC_UNLISTED_STATIC_ARM`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, unlisted-static-arm.
- Target: unlisted-static-arm; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3104` `CMD_DEL_PLAYLIST`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, special-0x3104-only, recognized zero-result special case.
- Target: recognized zero-result special case; reply: 4000.
- XDJ-RR: 1 direct call sites; wrappers dbcl_DelPlaylist; callers DBC_ReqUdPlaylist; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:9899` `DBC_ReqUdPlaylist` -> `dbcl_DelPlaylist` at `0x001fe428`, location `8` (call-argument-2).

### `3107` `CMD_GET_FILTER_CONDITION_PROPERTY`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnFilterCmd, get-filter-condition-property.
- Target: get-filter-condition-property; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3201` `CMD_SET_ONAIR`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnHistoryCmd, set-onair.
- Target: set-onair; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_SetOnAir; callers ReqRegistOnAir; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:2518` `ReqRegistOnAir` -> `dbcl_SetOnAir` at `0x00213cac`, location `8` (call-argument-2).

### `3202` `REKORDBOX_STATIC_UNLISTED_STATIC_ARM`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnPrepareCmd, unlisted-static-arm.
- Target: unlisted-static-arm; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_DelAllTaglist; callers DbReqAllDelTaglist; literal locations 6.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:4258` `DbReqAllDelTaglist` -> `dbcl_DelAllTaglist` at `0x00216504`, location `6` (wrapper-fixed).

### `3203` `CMD_GET_DB_FIRM_VER`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, get-db-firmware-version.
- Target: get-db-firmware-version; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3207` `CMD_SET_FILTER_CONDITION_PROPERTY`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnFilterCmd, set-filter-condition-property.
- Target: set-filter-condition-property; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3301` `CMD_DEL_HISTORY_REPLY`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnHistoryCmd, delete-history-reply.
- Target: delete-history-reply; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3302` `CMD_CHG_TAGLIST_ORDER`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnPrepareCmd, change-taglist-order.
- Target: change-taglist-order; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3303` `CMD_GET_BRWS_TYPE`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, get-browse-type.
- Target: get-browse-type; reply: -.
- XDJ-RR: 5 direct call sites; wrappers dbcl_GetBrowseType; callers ExecInfoJumpPrepare, GetBrowseKind, GetLeftPrepareList, GetRightPrepareList; literal locations 2.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:6323` `GetBrowseKind` -> `dbcl_GetBrowseType` at `0x001690b4`, location `2` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8578` `GetLeftPrepareList` -> `dbcl_GetBrowseType` at `0x0016c46c`, location `2` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8623` `GetLeftPrepareList` -> `dbcl_GetBrowseType` at `0x0016c46c`, location `2` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:8858` `GetRightPrepareList` -> `dbcl_GetBrowseType` at `0x0016c948`, location `2` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10263` `ExecInfoJumpPrepare` -> `dbcl_GetBrowseType` at `0x0020b810`, location `2` (wrapper-fixed).

### `3307` `CMD_SET_FILTER_CONDITION_MYTAG`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnFilterCmd, set-filter-condition-mytag.
- Target: set-filter-condition-mytag; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3401` `CMD_DEL_HISTORY_TRACK`

- Classification: `mutation-or-state-write`; coverage `real-rekordbox-menu-oracle`; evidence ALPHA, OBS, DB, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnHistoryCmd, delete-history-track.
- Target: delete-history-track; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_DelTrackHistory; callers SelectRightMenu; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:10311` `SelectRightMenu` -> `dbcl_DelTrackHistory` at `0x001fe73c`, location `1` (wrapper-fixed).

### `3402` `CMD_IS_TAGLIST_PLAYLIST`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnPrepareCmd, is-taglist-playlist.
- Target: is-taglist-playlist; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_CheckIsDBTrackExist; callers GetTaglistMenuList; literal locations 6.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:8455` `GetTaglistMenuList` -> `dbcl_CheckIsDBTrackExist` at `0x001fc1ec`, location `6` (wrapper-fixed).

### `3403` `REKORDBOX_STATIC_UNLISTED_STATIC_ARM`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, unlisted-static-arm.
- Target: unlisted-static-arm; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3407` `CMD_ADD_FILTER_MYTAG_ITEM`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnFilterCmd, add-filter-mytag-item.
- Target: add-filter-mytag-item; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3501` `CMD_GET_CURRENT_HISTORY_ID`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnHistoryCmd, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: 3501 is outside history-high-byte.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3503` `CMD_INFO_UNPLAYABLE`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, info-unplayable.
- Target: info-unplayable; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_SetUnplayable; callers SetUnPlayable; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:7212` `SetUnPlayable` -> `dbcl_SetUnplayable` at `0x001fa87c`, location `8` (call-argument-2).

### `3602` `CMD_REPLACE_TAGLIST`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnPrepareCmd, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: 3602 is outside prepare-high-byte.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3603` `CMD_GET_DB_HIERARCHY`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, get-db-hierarchy.
- Target: get-db-hierarchy; reply: -.
- XDJ-RR: 2 direct call sites; wrappers dbcl_GetDBHierachy; callers GetOffsetInCate, ReloadCateBrws; literal locations 7.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:10129` `GetOffsetInCate` -> `dbcl_GetDBHierachy` at `0x0020b674`, location `7` (call-argument-2).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0021.c:3281` `ReloadCateBrws` -> `dbcl_GetDBHierachy` at `0x00214c8c`, location `7` (call-argument-2).

### `3703` `REKORDBOX_STATIC_UNLISTED_STATIC_ARM`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, unlisted-static-arm.
- Target: unlisted-static-arm; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3704` `CMD_APPEND_PLAYLIST`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, special-0x3104-only, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: special-0x3104-only recognizes only 3104.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3803` `REKORDBOX_STATIC_UNLISTED_STATIC_ARM`

- Classification: `recognized-static-route`; coverage `rekordbox-static-dispatch`; evidence DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, unlisted-static-arm.
- Target: unlisted-static-arm; reply: -.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3804` `CMD_REPLACE_PLAYLIST_TRACK`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, special-0x3104-only, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: special-0x3104-only recognizes only 3104.
- XDJ-RR: 0 direct call sites; wrappers -; callers -; literal locations -.

### `3903` `CMD_PROPERTY_TABLE`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, property-table.
- Target: property-table; reply: -.
- XDJ-RR: 2 direct call sites; wrappers dbcl_GetPropTbl; callers UpDateDevProperty, UpDateDevProperty_BroadCast; literal locations 8.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:7191` `UpDateDevProperty` -> `dbcl_GetPropTbl` at `0x0016a4dc`, location `8` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:7248` `UpDateDevProperty_BroadCast` -> `dbcl_GetPropTbl` at `0x0016a578`, location `8` (wrapper-fixed).

### `3A03` `CMD_TRANS_NEWKEY`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, translate-new-key.
- Target: translate-new-key; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_TransNewKeyID; callers ExecInformationJump; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0020.c:11065` `ExecInformationJump` -> `dbcl_TransNewKeyID` at `0x0020c60c`, location `1` (wrapper-fixed).

### `3B03` `CMD_GET_PLAYSTATE`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, get-play-state.
- Target: get-play-state; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_GetTrackPlayState; callers SendBrowseMenu; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:9284` `SendBrowseMenu` -> `dbcl_GetTrackPlayState` at `0x001fd1d4`, location `1` (wrapper-fixed).

### `3C03` `CMD_SET_MY_SETTING_FLG`

- Classification: `mutation-or-state-write`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, set-my-setting-flag.
- Target: set-my-setting-flag; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_UpdateMySettingFileExist; callers ReqUpdate_MySettingFileExist; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:7320` `ReqUpdate_MySettingFileExist` -> `dbcl_UpdateMySettingFileExist` at `0x0016a734`, location `1` (wrapper-fixed).

### `3D03` `CMD_GET_NEW_KEY_ID`

- Classification: `state-query`; coverage `rekordbox-static-dispatch`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, get-new-key-id.
- Target: get-new-key-id; reply: -.
- XDJ-RR: 1 direct call sites; wrappers dbcl_GetNewKeyID; callers UpdateTrafficLightKeySet.part.0; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0017.c:6812` `UpdateTrafficLightKeySet.part.0` -> `dbcl_GetNewKeyID` at `0x00179e70`, location `1` (wrapper-fixed).

### `3E03` `CMD_GET_IS_RBM_MOUNT`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: 3E03 is outside other-command-high-byte.
- XDJ-RR: 1 direct call sites; wrappers dbcl_GetIsRekordboxMobile; callers DBC_NfsAnalysisStart; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_0016.c:6494` `DBC_NfsAnalysisStart` -> `dbcl_GetIsRekordboxMobile` at `0x0016932c`, location `1` (wrapper-fixed).

### `3F03` `CMD_SET_BACKGROUND_COLOR`

- Classification: `rejected`; coverage `rekordbox-static-rejected`; evidence ALPHA, DEC.
- Rekordbox route: PSvDBMain::OnOtherClientCmd, PSvDBMain::OnOtherCmd, PSvDBMain::OnUnknownClientCmd.
- Target: -; reply: 4003.
- Rejection: 3F03 is outside other-command-high-byte.
- XDJ-RR: 2 direct call sites; wrappers dbcl_SetBackGroundColor; callers SelectRightMenu, SendBrowseMenu; literal locations 1.
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:9526` `SendBrowseMenu` -> `dbcl_SetBackGroundColor` at `0x001fd1d4`, location `1` (wrapper-fixed).
- Caller evidence: `alphatheta-docs/devices/xdj-rr/application/assets/decompiled/_unattributed/chunk_001f.c:10181` `SelectRightMenu` -> `dbcl_SetBackGroundColor` at `0x001fe73c`, location `1` (wrapper-fixed).

## Interpretation boundary

The Rekordbox side records server behavior at its stated evidence tier.
The XDJ-RR side is a client-source inventory, not evidence that every other
device uses the same call path. A missing XDJ-RR caller is preserved as zero
rather than promoted to a cross-device negative conclusion.

The coarse effect class is an index. Exact route, target, database and
filesystem dependencies, replies, rejection reasons, and evidence labels are
authoritative. Live outcome gaps remain in `REKORDBOX_RESEARCH_GAPS.md`.

Regenerate both artifacts with:

```sh
./.venv/bin/python tools/generate_control_mutation_reference.py
```
