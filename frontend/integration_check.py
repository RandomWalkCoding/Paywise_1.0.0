import json
import os
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright

BASE = os.getenv("PAYWISE_FRONTEND_URL", "http://127.0.0.1:5173")
API = os.getenv("PAYWISE_API_URL", "http://127.0.0.1:8000/api/v1")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    prefix = f"integration-{uuid4().hex[:8]}"
    created_ids = []

    def calculate():
        page.get_by_role("button", name="计算到手收入", exact=True).click()
        expect(page.get_by_role("heading", name="计算结果", exact=True)).to_be_visible()

    def save(name):
        page.get_by_role("textbox", name="方案名称").fill(name)
        with page.expect_response(lambda response: response.url.endswith("/scenarios") and response.request.method == "POST") as saved:
            page.get_by_role("button", name="保存方案", exact=True).click()
        assert saved.value.ok
        created_ids.append(saved.value.json()["id"])
        expect(page.get_by_role("status")).to_have_text("方案已保存")

    try:
        page.goto(BASE, wait_until="networkidle")
        page.get_by_role("link", name="开始计算").click()
        calculate()
        expect(page.locator(".result-grid strong").filter(has_text="到手现金")).to_contain_text("16155.00")
        page.get_by_label("累计预扣月份", exact=True).fill("2")
        expect(page.get_by_role("heading", name="计算结果", exact=True)).to_have_count(0)
        page.get_by_label("累计预扣月份", exact=True).fill("1")
        calculate()
        first = prefix + "-A"
        save(first)
        page.reload(wait_until="networkidle")
        page.get_by_role("button", name=first).click()
        expect(page.get_by_label("月固定工资", exact=True)).to_have_value("20000")
        row = page.locator(".scenario-row").filter(has_text=first)
        row.get_by_role("button", name="复制", exact=True).click()
        expect(page.get_by_label("方案名称", exact=True)).to_have_value(first + " 副本")
        page.get_by_label("月固定工资", exact=True).fill("25000")
        calculate()
        second = prefix + "-B"
        save(second)
        row = page.locator(".scenario-row").filter(has_text=second)
        renamed = prefix + "-renamed"
        page.once("dialog", lambda dialog: dialog.accept(renamed))
        row.get_by_role("button", name="重命名", exact=True).click()
        row = page.locator(".scenario-row").filter(has_text=renamed)
        expect(row).to_be_visible()
        page.once("dialog", lambda dialog: dialog.accept())
        row.get_by_role("button", name="删除", exact=True).click()
        expect(page.get_by_role("status")).to_have_text("方案已移入回收站")
        page.locator(".trash summary").click()
        page.locator(".scenario-row.deleted").filter(has_text=renamed).get_by_role("button", name="恢复").click()
        expect(page.get_by_role("status")).to_have_text("方案已恢复")
        with page.expect_download() as download:
            page.get_by_role("button", name="导出结果", exact=True).click()
        payload = json.loads(Path(download.value.path()).read_text(encoding="utf-8"))
        assert "summary" in payload
        assert not {"input_snapshot", "monthly_salary", "work_city", "breakdown"} & payload.keys()
        page.get_by_role("button", name="复制脱敏摘要", exact=True).click()
        expect(page.get_by_role("status")).to_have_text("脱敏结果摘要已复制")
        share = page.evaluate("navigator.clipboard.readText()")
        assert "到手现金" in share and "月固定工资" not in share
        for index in range(3):
            save(prefix + f"-extra-{index}")
        page.get_by_role("link", name="Offer 对比", exact=True).click()
        expect(page.locator(".offer-picker-row").filter(has_text=first)).to_be_visible()
        for name in [first, renamed, prefix + "-extra-0", prefix + "-extra-1"]:
            page.locator(".offer-picker-row").filter(has_text=name).click()
        expect(page.locator(".comparison-table thead th")).to_have_count(5)
        expect(page.locator(".value-skeleton")).to_have_count(0)
        page.locator(".offer-picker-row").filter(has_text=prefix + "-extra-2").click()
        expect(page.get_by_role("alert")).to_have_text("最多选择 4 个方案进行对比。")
        expect(page.locator(".offer-picker-row input:checked")).to_have_count(4)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.set_viewport_size({"width": 1280, "height": 900})
        assert not errors, errors
        # Deterministic empty and failure states, without changing existing user scenarios.
        page.route("**/api/v1/scenarios?*", lambda route: route.fulfill(json=[]))
        page.reload(wait_until="networkidle")
        expect(page.get_by_role("heading", name="还没有可比较的方案")).to_be_visible()
        page.unroute("**/api/v1/scenarios?*")
        page.route("**/api/v1/scenarios?*", lambda route: route.fulfill(status=503, json={"message": "unavailable"}))
        page.reload(wait_until="networkidle")
        expect(page.get_by_role("heading", name="方案加载失败")).to_be_visible()
        page.unroute("**/api/v1/scenarios?*")
        page.goto(BASE + "/calculator", wait_until="networkidle")
        page.route("**/api/v1/calculations", lambda route: route.fulfill(status=503, json={"message": "unavailable"}))
        page.get_by_role("button", name="计算到手收入", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("503")
        expect(page.get_by_role("heading", name="计算结果", exact=True)).to_have_count(0)
        print("PASS: fixed calculation, stale result invalidation, save/reload/copy/rename/delete/restore, export, clipboard, four-offer limit, mobile layout, empty/error states")
    finally:
        for scenario_id in created_ids:
            response = context.request.delete(f"{API}/scenarios/{scenario_id}")
            assert response.ok
        browser.close()

