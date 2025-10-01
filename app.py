kode = None
nama_wilayah = None

# --- Input manual ---
if user_input:
    try:
        desa, kecamatan = [x.strip().lower() for x in user_input.split(",")]
        match = wilayah_df[wilayah_df["nama"].str.lower().str.contains(desa)]
        if not match.empty:
            kode = match.iloc[0]["kode"]
            nama_wilayah = match.iloc[0]["nama"]
            st.success(f"✅ Ditemukan kode wilayah (input manual): {kode} ({nama_wilayah})")
    except Exception:
        st.warning("⚠️ Format: Desa, Kecamatan")

# --- Klik peta ---
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.write(f"📍 Koordinat dipilih: {lat:.4f}, {lon:.4f}")

    geolocator = Nominatim(user_agent="bmkg-app")
    loc = geolocator.reverse((lat, lon), language="id")
    if loc:
        nama_search = loc.raw.get("address", {}).get("village") or loc.raw.get("address", {}).get("town") or ""
        nama_search = nama_search.lower()
        match = wilayah_df[wilayah_df["nama"].str.lower().str.contains(nama_search)]
        if not match.empty:
            kode_peta = match.iloc[0]["kode"]
            nama_peta = match.iloc[0]["nama"]
            st.success(f"✅ Ditemukan kode wilayah (klik peta): {kode_peta} ({nama_peta})")

            # kalau user MAU pakai hasil peta → timpa kode manual
            if st.button("Gunakan hasil dari peta"):
                kode = kode_peta
                nama_wilayah = nama_peta
