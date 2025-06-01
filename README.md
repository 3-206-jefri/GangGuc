# GangGuc
Tubes Stimma 

1. Penjelasan Singkat




2.Requirment Program atau installasi
  -Install Docker Desktop melalui link : https://www.docker.com/products/docker-desktop/
  -Install NodeJs Melalui link:  https://nodejs.org/en
  -Install Yarn menggunakan command prompt , dengan command : npm install --global yarn
  -Extract dan Install Game Engine  berupa (.zip) pada link berikut : https://github.com/haziqam/tubes1-IF2211-game-engine/releases/tag/v1.1.0
  -Extract Bot Starter pack (.zip) pada link berikut : https://github.com/haziqam/tubes1-IF2211-bot-starter-pack/releases/tag/v1.0.1

3. Command atau langkah langkah untuk mengcompile program
  -Masuk ke root directory menggunakan cmd prompt dimana pathnya sesuai dengan folder game engine yang sudah di extract
  -lalu jalankan command yarn di directory
  -SetUp Default Environment Menggukaan script berikut
    Windows : scripts\copy-env.bat
    Linux : chmod +x ./scripts/copy-env.sh
            ./scripts/copy-env.sh
  -Selanjutnya buka docker desktop dan jalankan command : docker compose up -d database
  -Selanjutnya jalankan script :
   Windows : scripts\setup-db-prisma.bat
   Linux : chmod +x ./scripts/setup-db-prisma.sh
           ./scripts/setup-db-prisma.sh
   -Lalu Build npm di cmd prompt dengan command : npm run build
   -Setelah npm di build kita start npm nya dengan command : npm run start
   -Jika berhasil kita buka link frontend melalui link : http://localhost:8082/
   -Setelah frontend di buka buka cmd baru dan masuk ke path directory bot starterpack yang sudah di extract
   -Lalu install dependencies menggunakan pip , dengan command : pip install -r requirements.txt
   -Selanjutnya untuk menjalankan satu bot kita bisa menggunakan command seperti ini yang di jalankan di cmd baru :
     python main.py --logic Slamet --email=your_email@example.com --name=your_name --password=your_password --team etimo
     python main.py --logic Jamal --email=your_email@example.com --name=your_name --password=your_password --team etimo
     Dimana Email , nama serta passwordnya bisa di custom sesuai dengan keinginan kamu.
   -Untuk menjalankan 4 bot  dengan logic yang berbeda ,kamu bisa run  command seperti ini yang di jalankan di cmd baru:
     ./run-bots.bat
    jika kamu ingin mengcustom nama, email , dan password kalian bisa masuk ke file bots.bat  dan ganti bagian Nama , email dan password
   
