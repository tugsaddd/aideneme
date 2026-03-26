# 🤖 Yerel AI (Local AI)

Kendi bilgisayarınızda çalışan, **Ollama** destekli yapay zeka sohbet uygulaması.  
Hem güzel bir **web arayüzü** hem de **komut satırı (CLI)** arayüzü içerir.

---

## 📋 Gereksinimler

| Bileşen | Versiyon |
|---------|----------|
| Python  | ≥ 3.10   |
| [Ollama](https://ollama.ai) | Son sürüm |

---

## ⚡ Hızlı Başlangıç

### 1. Ollama'yı Kurun

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows – https://ollama.ai adresinden indirin
```

### 2. Bir Model İndirin

```bash
ollama pull llama3.2          # önerilen – 2 GB
# veya
ollama pull mistral           # alternatif – 4 GB
# veya
ollama pull phi3              # hafif model – 1.7 GB
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Uygulamayı Başlatın

**Web arayüzü (tarayıcıda sohbet):**
```bash
python app.py
# Tarayıcıda açın → http://127.0.0.1:8000
```

**Komut satırı:**
```bash
python cli.py
# veya belirli bir model ile:
python cli.py --model mistral
# veya özel sistem mesajı ile:
python cli.py --model llama3.2 --system "Sen bir Python uzmanısın"
```

---

## 🗂️ Proje Yapısı

```
aideneme/
├── app.py             # FastAPI web sunucusu
├── cli.py             # Komut satırı arayüzü
├── ollama_client.py   # Ollama API istemcisi
├── config.py          # Yapılandırma yükleyici
├── config.yaml        # Ayar dosyası
├── requirements.txt
├── templates/
│   └── index.html     # Web arayüzü şablonu
├── static/
│   ├── style.css      # Koyu tema CSS
│   └── app.js         # Frontend JavaScript
└── tests/
    └── test_app.py    # Birim testler
```

---

## ⚙️ Yapılandırma

`config.yaml` dosyasını düzenleyerek ayarları değiştirebilirsiniz:

```yaml
ollama:
  base_url: "http://localhost:11434"  # Ollama adresi
  default_model: "llama3.2"           # Varsayılan model
  timeout: 120                        # Zaman aşımı (saniye)

server:
  host: "127.0.0.1"
  port: 8000

chat:
  system_prompt: "Sen yardımcı bir yapay zeka asistanısın..."
  max_history: 20     # Bellekte tutulan mesaj sayısı
  stream: true        # Gerçek zamanlı akış
```

---

## 🧪 Testleri Çalıştırma

```bash
pip install pytest httpx
pytest tests/ -v
```

---

## 🌐 Web Arayüzü Özellikleri

- 🌙 Koyu tema
- 💬 Gerçek zamanlı akışlı yanıtlar (streaming)
- 🔄 Model seçimi (yüklü tüm modeller listelenir)
- 📝 Özelleştirilebilir sistem mesajı
- 🗑️ Yeni sohbet başlatma
- 📱 Mobil uyumlu

## 💻 CLI Özellikleri

- 🎨 Renkli terminal çıktısı (Rich kütüphanesi)
- ⚡ Gerçek zamanlı akışlı yanıtlar
- 🔧 Model ve sistem mesajı seçimi
- `/temizle` komutu ile sohbet sıfırlama
- `/modeller` komutu ile yüklü modelleri listeleme

---

## 🔍 Sorun Giderme

**"Ollama çalışmıyor" hatası:**
```bash
ollama serve          # Ollama'yı başlat
ollama list           # Yüklü modelleri gör
ollama pull llama3.2  # Model indir
```

**Port zaten kullanımda:**
`config.yaml` içinde `server.port` değerini değiştirin.
