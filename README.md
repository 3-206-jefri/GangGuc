# GangGuc

## Tugas Besar STIMMA

---

## 1. Penjelasan Singkat

GangGuc merupakan proyek Tugas Besar mata kuliah Strategi Teknik Informatika Strategi Algoritma yang melibatkan pengembangan bot AI untuk bermain dalam game berbasis maze dengan strategi tertentu. Bot diimplementasikan menggunakan Python dan berinteraksi dengan game engine berbasis web menggunakan API.

---

## 2. Requirement Program dan Instalasi

### Software yang Diperlukan:

- **Docker Desktop**  
  [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)

- **Node.js**  
  [Download Node.js](https://nodejs.org/en)

- **Yarn**  
  Install via Command Prompt:  
  ```bash
  npm install --global yarn
  ```

- **Game Engine (.zip)**  
  [Download Game Engine v1.1.0](https://github.com/haziqam/tubes1-IF2211-game-engine/releases/tag/v1.1.0)

- **Bot Starter Pack (.zip)**  
  [Download Bot Starter Pack v1.0.1](https://github.com/haziqam/tubes1-IF2211-bot-starter-pack/releases/tag/v1.0.1)

---

## 3. Langkah-Langkah untuk Menjalankan Program

### Setup Game Engine:

1. **Masuk ke folder hasil extract Game Engine** menggunakan Command Prompt.
2. Jalankan perintah:
   ```bash
   yarn
   ```
3. **Setup Default Environment:**
   - Untuk Windows:
     ```bash
     scripts\copy-env.bat
     ```
   - Untuk Linux:
     ```bash
     chmod +x ./scripts/copy-env.sh
     ./scripts/copy-env.sh
     ```

4. **Buka Docker Desktop**, lalu jalankan:
   ```bash
   docker compose up -d database
   ```

5. Jalankan setup database:
   - Untuk Windows:
     ```bash
     scripts\setup-db-prisma.bat
     ```
   - Untuk Linux:
     ```bash
     chmod +x ./scripts/setup-db-prisma.sh
     ./scripts/setup-db-prisma.sh
     ```

6. **Build dan Start Game Engine:**
   ```bash
   npm run build
   npm run start
   ```

7. Buka browser dan akses frontend game melalui:  
   [http://localhost:8082/](http://localhost:8082/)

---

### Setup dan Menjalankan Bot:

1. Masuk ke folder hasil extract **Bot Starter Pack**.
2. Install dependencies Python:
   ```bash
   pip install -r requirements.txt
   ```

3. **Menjalankan Satu Bot:**
   Jalankan command berikut di terminal baru:
   ```bash
   python main.py --logic Slamet --email=your_email@example.com --name=your_name --password=your_password --team etimo
   python main.py --logic Jamal --email=your_email@example.com --name=your_name --password=your_password --team etimo
   ```

   > Gantilah `your_email`, `your_name`, dan `your_password` sesuai keinginanmu.

4. **Menjalankan Empat Bot Sekaligus:**
   Jalankan script batch berikut di terminal baru:
   ```bash
   ./run-bots.bat
   ```

   Untuk mengganti nama, email, atau password bot, edit file `run-bots.bat` dan sesuaikan bagian:
   ```bat
   --name=your_name --email=your_email --password=your_password
   ```

---

## Selamat Bermain dan Semoga Sukses!
