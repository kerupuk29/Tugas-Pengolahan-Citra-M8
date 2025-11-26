import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# --- Konfigurasi Halaman ---
st.set_page_config(layout="wide", page_title="Steganografi Citra: LSB", page_icon="🕵️")

st.title("🕵️ Steganografi: Sembunyikan Pesan dalam Gambar")
st.markdown("""
Aplikasi ini menggunakan teknik **Least Significant Bit (LSB)**. 
Kita menyisipkan pesan rahasia ke dalam piksel gambar tanpa merusak tampilan visualnya.
""")

# --- Fungsi Logika Steganografi (Backend) ---

def to_bin(data):
    """Konversi data (string/int) ke format biner."""
    if isinstance(data, str):
        return ''.join([format(ord(i), "08b") for i in data])
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [format(i, "08b") for i in data]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, "08b")
    else:
        raise TypeError("Input type not supported")

def encode_data(image, secret_data):
    """Menyisipkan teks ke dalam gambar."""
    # Hitung byte maksimum yang bisa disimpan
    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    if len(secret_data) > n_bytes:
        raise ValueError("Error: Ukuran teks terlalu besar untuk gambar ini!")

    # Tambahkan delimiter '#####' untuk menandai akhir pesan
    secret_data += "#####"
    
    data_index = 0
    binary_secret_data = to_bin(secret_data)
    data_len = len(binary_secret_data)
    
    encoded_image = image.copy()
    
    for row in encoded_image:
        for pixel in row:
            # pixel adalah array [R, G, B]
            for i in range(3): # Loop r, g, b
                if data_index < data_len:
                    # Ubah bit terakhir (LSB) piksel sesuai bit data pesan
                    pixel[i] = int(to_bin(pixel[i])[:-1] + binary_secret_data[data_index], 2)
                    data_index += 1
                else:
                    return encoded_image
    return encoded_image

def decode_data(image):
    """Mengekstrak teks dari gambar."""
    binary_data = ""
    for row in image:
        for pixel in row:
            for i in range(3): # Loop r, g, b
                binary_data += to_bin(pixel[i])[-1] # Ambil bit terakhir

    # Kelompokkan menjadi 8 bit (1 byte)
    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    
    decoded_data = ""
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        # Cek delimiter
        if decoded_data[-5:] == "#####":
            return decoded_data[:-5] # Hapus delimiter dan kembalikan pesan
            
    return "Tidak ada pesan tersembunyi yang ditemukan (atau format salah)."

# --- Antarmuka Pengguna (Frontend) ---

tab1, tab2 = st.tabs(["🔒 Enkripsi (Sembunyikan)", "🔓 Dekripsi (Buka Pesan)"])

# === TAB 1: ENKRIPSI ===
with tab1:
    st.header("Sembunyikan Pesan")
    
    col_up, col_txt = st.columns([1, 1])
    
    with col_up:
        uploaded_file = st.file_uploader("1. Upload Gambar Asli (PNG/JPG)", type=["png", "jpg", "jpeg"], key="upload_enc")
    
    with col_txt:
        secret_text = st.text_area("2. Tulis Pesan Rahasia Anda", placeholder="Contoh: Kode nuklir ada di bawah kasur.")

    if uploaded_file is not None and secret_text:
        # Baca Gambar
        image = Image.open(uploaded_file)
        img_array = np.array(image) # Konversi ke Numpy
        
        # Tombol Proses
        if st.button("🔒 Lakukan Steganografi", type="primary"):
            try:
                with st.spinner("Sedang menyisipkan pesan..."):
                    encoded_image = encode_data(img_array, secret_text)
                    
                    st.success("Berhasil! Pesan telah disembunyikan.")
                    st.divider()
                    
                    # Tampilkan Hasil Side-by-Side
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Citra Awal")
                        st.image(image, caption="Gambar Original", use_container_width=True)
                    with c2:
                        st.subheader("Citra Hasil Stegano")
                        st.image(encoded_image, caption=f"Gambar + Pesan: '{secret_text}'", use_container_width=True)
                    
                    # Konversi hasil ke bytes untuk didownload
                    result_img_pil = Image.fromarray(encoded_image)
                    buf = io.BytesIO()
                    # PENTING: Harus disimpan sebagai PNG agar kompresi tidak merusak data LSB
                    result_img_pil.save(buf, format="PNG") 
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="⬇️ Download Gambar Hasil Stegano (.png)",
                        data=byte_im,
                        file_name="stegano_image.png",
                        mime="image/png"
                    )
                    st.warning("⚠️ Penting: Simpan dalam format PNG. Jika dikonversi ke JPG/WA, pesan akan rusak/hilang karena kompresi.")
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# === TAB 2: DEKRIPSI ===
with tab2:
    st.header("Baca Pesan Tersembunyi")
    
    dec_file = st.file_uploader("Upload Gambar Stegano (.PNG)", type=["png"], key="upload_dec")
    
    if dec_file is not None:
        image_dec = Image.open(dec_file)
        img_array_dec = np.array(image_dec)
        
        st.image(image_dec, caption="Gambar yang diupload", width=300)
        
        if st.button("🔓 Dekripsi / Baca Pesan"):
            with st.spinner("Sedang mencari pesan..."):
                hidden_message = decode_data(img_array_dec)
                
                if "Tidak ada pesan" in hidden_message:
                    st.error(hidden_message)
                else:
                    st.success("Pesan ditemukan!")
                    st.balloons()
                    st.markdown(f"### 📜 Pesan Rahasia:")
                    st.code(hidden_message, language="text")
