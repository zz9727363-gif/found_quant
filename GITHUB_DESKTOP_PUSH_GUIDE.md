# 用 GitHub Desktop 推送到 `found-quant`

1. 打开 **GitHub Desktop**，选择 **File → Add local repository**。
2. 选择本地文件夹：`C:\Users\ace\Desktop\found_quant`。
3. 左下角填写提交说明：`add cloud workflow`。
4. 点击 **Commit to main**。
5. 点击顶部 **Publish repository**。
6. 仓库名填写 `found-quant`，选择你的 GitHub 账号；按你的需要选择公开或私有，然后点击发布。
7. 打开 GitHub 网页上的 `found-quant` 仓库，确认能看到：
   - `.github/workflows/ndx_price.yml`
   - `ndx_price.py`
8. 在仓库页面进入 **Settings → Secrets and variables → Actions**，点击 **New repository secret**：
   - Name：`PUSHPLUS_TOKEN`
   - Secret：粘贴你的 PushPlus Token
   - 点击 **Add secret**
9. 回到仓库的 **Actions** 页面，选择“纳指定投计算与微信推送”，点击 **Run workflow** 手动测试一次。

之后 GitHub Actions 会按每天北京时间 14:30（UTC 06:30）自动运行。
