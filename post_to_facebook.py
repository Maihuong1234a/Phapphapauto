#!/usr/bin/env python3
# ============================================================
# AUTO POST PHAT PHAP - Dang bai len Facebook tu GitHub Actions
# ============================================================

import os
import json
import random
import requests
import glob
from datetime import datetime, timezone, timedelta

# ---- Cau hinh ----
PAGE_ID     = os.environ.get("PAGE_ID", "1312014271988713")
USER_TOKEN  = os.environ.get("USER_TOKEN", "")
PAGE_TOKEN  = os.environ.get("PAGE_TOKEN", "")
IMAGE_FOLDER = "images"   # Thu muc chua anh trong repo GitHub
LOG_FILE     = "post_log.json"

# Múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))


# ---- Lấy Page Token mới từ User Token ----
def get_fresh_page_token():
    try:
        url = "https://graph.facebook.com/v19.0/me/accounts"
        print(f"[INFO] Dang lay Page Token tu User Token...")
        resp = requests.get(url, params={"access_token": USER_TOKEN}, timeout=10)
        data = resp.json()
        print(f"[DEBUG] Phan hoi tu Facebook: {json.dumps(data)[:300]}")
        if "error" in data:
            err = data["error"]
            print(f"[ERROR] User Token bi loi: code={err.get('code')} msg={err.get('message')}")
            print(f"[ERROR] Token het han! Can lay token moi tu Facebook Graph Explorer")
            print(f"[ERROR] Vao: https://developers.facebook.com/tools/explorer/")
        elif "data" in data and len(data["data"]) > 0:
            token = data["data"][0]["access_token"]
            print(f"[OK] Lay Page Token moi thanh cong! Page: {data['data'][0].get('name','')}")
            return token
        else:
            print(f"[WARN] Khong tim thay Page nao trong tai khoan")
    except Exception as e:
        print(f"[WARN] Khong lay duoc Page Token moi: {e}")
    print(f"[INFO] Dung Page Token co san tu SECRET")
    return PAGE_TOKEN


# ---- Đọc log ----
def read_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"posted": []}


# ---- Ghi log ----
def write_log(log):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ---- Lấy danh sách ảnh ----
def get_image_list():
    extensions = ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG"]
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(IMAGE_FOLDER, ext)))
    images = sorted(set(images))
    return images


# ---- Lấy ảnh tiếp theo chưa đăng ----
def get_next_image(log):
    images = get_image_list()
    if not images:
        print("[ERROR] Khong tim thay anh nao trong thu muc 'images/'!")
        return None

    posted = log.get("posted", [])
    image_names = [os.path.basename(img) for img in images]

    # Tìm ảnh chưa đăng
    for img_path in images:
        name = os.path.basename(img_path)
        if name not in posted:
            return img_path

    # Hết ảnh → reset và bắt đầu lại
    print("[INFO] Da dang het toan bo anh! Bat dau lai tu dau...")
    log["posted"] = []
    write_log(log)
    return images[0] if images else None


# ---- Tạo caption theo giờ VN ----
def get_caption():
    now_vn = datetime.now(VN_TZ)
    hour = now_vn.hour
    print(f"[INFO] Gio VN hien tai: {now_vn.strftime('%H:%M')} - Chon caption phu hop")

    captions_sang = [
        "🌅 CHÀO NGÀY MỚI AN LÀNH 🌅\n\nMỗi buổi sáng là một trang giấy trắng — hãy viết lên đó những điều tốt đẹp bằng tâm từ bi và trí tuệ.\n\n🙏 Đức Phật dạy:\n\"Tâm bình thì thế giới bình. Hãy bắt đầu ngày mới bằng một nụ cười và lòng biết ơn.\"\n\n🌸 Nguyện cho ngày mới của bạn tràn đầy an vui và may mắn!\n\n#ChaoNgayMoi #PhatPhap #BinhAn #LoiPhatMoiNgay",
        "☀️ NAM MÔ BỔN SƯ THÍCH CA MÂU NI PHẬT ☀️\n\nBuổi sáng thanh tịnh — hãy dành vài phút ngồi yên, lắng nghe hơi thở, để tâm trở về với hiện tại.\n\n✨ Một ngày bắt đầu trong chánh niệm là một ngày sống trọn vẹn.\n\n🌺 Chúc quý Phật tử một ngày an lạc, vạn sự như ý!\n\n#CanhNiem #ThienDinh #PhatPhap #BinhAn",
        "🙏 KÍNH CHÀO QUÝ PHẬT TỬ 🙏\n\nMỗi bình minh là ân huệ Phật ban cho ta thêm một ngày để tu tập và làm điều thiện.\n\n💛 Đừng để ngày trôi qua vô ích — hãy gieo một hạt giống thiện lành hôm nay.\n\n🌸 Nam Mô Bổn Sư Thích Ca Mâu Ni Phật 🌸\n\n#NamMoPhat #ThienLanh #PhatPhap #LoiPhatMoiNgay",
    ]

    captions_trua = [
        "🌿 LỜI PHẬT GIỮA NGÀY 🌿\n\nGiữa bộn bề công việc, hãy nhớ:\n\n💭 Đức Phật dạy: \"Không có con đường nào dẫn đến hạnh phúc — hạnh phúc chính là con đường.\"\n\n🌺 Hãy mỉm cười với những gì bạn đang có. Biết ơn là cánh cửa dẫn đến bình an.\n\n👇 Chia sẻ nếu bạn thấy ý nghĩa!\n\n#LoiPhat #HanhPhuc #BinhAn #PhatPhap",
        "⚡ NĂNG LƯỢNG GIỮA NGÀY ⚡\n\nKhi tâm bạn bình — mọi việc đều nhẹ nhàng.\nKhi tâm bạn loạn — mọi việc đều nặng nề.\n\n🧘 Dành 1 phút giữa ngày để hít thở sâu, thả lỏng vai, buông bỏ phiền muộn.\n\n🌸 Bạn xứng đáng được sống trong bình an! 🙏\n\n#ThienDinh #CanhNiem #PhatPhap #NamMoPhat",
        "🪷 TRÍ TUỆ PHẬT PHÁP 🪷\n\nĐức Phật dạy về Vô Thường:\n\n\"Mọi thứ đều thay đổi — đừng bám víu vào điều gì quá chặt, vì sự bám víu chính là nguồn gốc của khổ đau.\"\n\n💡 Hiểu được vô thường, ta sẽ trân trọng hơn từng khoảnh khắc của cuộc sống.\n\n#VoThuong #TriTue #PhatPhap #LoiPhatMoiNgay",
    ]

    captions_chieu = [
        "🌤️ CHIỀU AN LÀNH 🌤️\n\nBuổi chiều nhắc nhở ta: Một ngày sắp qua — bạn đã làm được điều gì tốt đẹp chưa?\n\n💚 Dù nhỏ bé đến đâu — một nụ cười, một lời động viên, một cử chỉ yêu thương... đều là hạt giống thiện lành.\n\n🙏 Hãy gieo thêm yêu thương vào chiều hôm nay!\n\n#ThienLanh #YeuThuong #PhatPhap #BinhAn",
        "🍃 SUY NGẪM CUỐI NGÀY 🍃\n\nĐức Phật dạy:\n\"Kẻ thù lớn nhất của bạn không phải là người khác — mà chính là tâm sân hận, tham lam và si mê bên trong.\"\n\n🌺 Hãy chinh phục bản thân trước khi chinh phục thế giới.\n\n👇 CHIA SẺ cho người thân cùng đọc nhé!\n\n#LoiPhat #NguHoanh #PhatPhap #TriTue",
        "☘️ PHẬT PHÁP NHIỆM MẦU ☘️\n\nTứ Diệu Đế — 4 sự thật mà Đức Phật giác ngộ:\n\n1️⃣ Khổ — Cuộc đời có khổ đau\n2️⃣ Tập — Khổ đau có nguyên nhân\n3️⃣ Diệt — Có thể chấm dứt khổ đau\n4️⃣ Đạo — Con đường thoát khổ\n\n🙏 Phật Pháp như ánh sáng soi đường cho chúng sinh.\n\n#TuDieuDe #PhatPhap #LoiPhatMoiNgay #NamMoPhat",
    ]

    captions_toi = [
        "🌙 BÌNH AN ĐÊM VỀ 🌙\n\nKhép lại một ngày — hãy dành vài phút cảm ơn:\n\n🙏 Cảm ơn vì còn được thở\n🙏 Cảm ơn vì còn có người thân\n🙏 Cảm ơn vì điều tốt đẹp đã xảy ra hôm nay\n\n✨ Ngủ ngon, ngủ bình an. Ngày mai sẽ là một ngày tươi đẹp hơn!\n\n#BiNgon #BinhAn #PhatPhap #LoiPhatMoiNgay",
        "🕯️ LỜI PHẬT ĐÊM KHUYA 🕯️\n\n\"Hãy là ngọn đèn cho chính mình. Hãy tự mình nương tựa vào chính mình.\"\n— Đức Phật Thích Ca —\n\n💛 Đêm nay trước khi ngủ, hãy tắt điện thoại sớm hơn, ngồi yên một chút, và lắng nghe trái tim mình.\n\n🌸 Chúc quý Phật tử một đêm an lành!\n\n#DemBinhAn #PhatPhap #NamMoPhat #LoiPhatMoiNgay",
        "🌟 KẾT THÚC NGÀY TỐT LÀNH 🌟\n\nTrước khi ngủ, hãy nhớ:\n\n💭 Điều gì tốt bạn đã làm hôm nay?\n💭 Ai bạn đã mang lại nụ cười?\n💭 Điều gì bạn biết ơn?\n\n🙏 Mỗi ngày sống đúng với Phật Pháp là một ngày ý nghĩa.\n\nNguyện cho tất cả chúng sinh được an lạc! 🌺\n\n#PhatPhap #NamMoPhat #BinhAn #LoiPhatMoiNgay",
    ]

    if 5 <= hour < 10:
        pool = captions_sang
        label = "Buoi sang"
    elif 10 <= hour < 15:
        pool = captions_trua
        label = "Buoi trua"
    elif 15 <= hour < 19:
        pool = captions_chieu
        label = "Buoi chieu"
    else:
        pool = captions_toi
        label = "Buoi toi"

    caption = random.choice(pool)
    print(f"[INFO] Caption da chon: {label}")
    return caption


# ---- Đăng lên Facebook ----
def post_to_facebook(image_path, caption, token):
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos"
    print(f"[INFO] Dang upload anh: {os.path.basename(image_path)}")

    with open(image_path, "rb") as img_file:
        # Xác định MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"

        resp = requests.post(
            url,
            data={"access_token": token, "message": caption},
            files={"source": (os.path.basename(image_path), img_file, mime)},
            timeout=60,
        )

    result = resp.json()
    print(f"[API] Ket qua: {result}")
    return result


# ---- Main ----
def main():
    now_vn = datetime.now(VN_TZ)
    print("=" * 60)
    print(f"  AUTO POST PHAT PHAP - {now_vn.strftime('%Y-%m-%d %H:%M')} VN")
    print("=" * 60)

    # Đọc log
    log = read_log()

    # Lấy ảnh tiếp theo
    image_path = get_next_image(log)
    if not image_path:
        print("[ERROR] Khong co anh de dang!")
        exit(1)

    # Lấy token mới
    token = get_fresh_page_token()

    # Tạo caption
    caption = get_caption()

    # Đăng bài
    result = post_to_facebook(image_path, caption, token)

    # Kiểm tra kết quả
    if result.get("post_id") or result.get("id"):
        post_id = result.get("post_id") or result.get("id")
        print(f"[THANH CONG] Da dang bai! Post ID: {post_id}")
        print(f"[INFO] Anh: {os.path.basename(image_path)}")

        # Cập nhật log
        log["posted"].append(os.path.basename(image_path))
        write_log(log)
        print(f"[INFO] Da cap nhat post_log.json")
    else:
        error = result.get("error", {})
        print(f"[THAT BAI] Loi: {error.get('message', str(result))}")
        exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
