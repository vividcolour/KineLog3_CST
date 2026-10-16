## Downloads

| File | What it is |
|---|---|
| **`Color-Space-Transform-mk2.dctl`** | The main DCTL: like Resolve's CST, with Kinefinity KineLog3 and DJI D-Log added |
| **`Color-Remap-mk2.dctl`** | One-node Kinefinity / DJI footage → ARRI LogC3 (any EI), LogC4, DaVinci Intermediate or KineLog3 |
| `Color-Space-Transform-mk2-Installer.zip` | Both DCTLs + extras + one-click installers for macOS and Windows |
| `Color-Space-Transform-mk2-DCTL-only.zip` | Both DCTLs + extras, no scripts, for manual install |
| `SHA256SUMS.txt` | Checksums, to verify your download |

Ignore the "Source code" downloads; they're the developer files.

**Install the DCTLs:**
1. In Resolve, go to **Project Settings > Color Management > Lookup Tables** and click **Open LUT Folder**.
2. Drop the `.dctl` files in.
3. Click **Update Lists**.

Or use the Installer zip.

This requires **DaVinci Resolve Studio**. See the [README](https://github.com/vividcolour/KineLog3_CST#readme) for supported cameras and usage, and the [CHANGELOG](https://github.com/vividcolour/KineLog3_CST/blob/main/CHANGELOG.md) for what's new.
