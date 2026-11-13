# 项目状态与确认记录

在课程项目目录保存 `course_state.json`，不写入技能目录。用于续作时知道哪份成果获确认、下一段接到哪里；不是让用户额外填写表格。

按需精简下列结构。初始值表示尚未确认；只有收到针对当前成果的明确答复才填写确认记录，不把模板当审批。

```json
{
  "course": {"topic": null, "audience": null, "lesson_count": null, "planned_minutes": null},
  "current_stage": "outline",
  "artifacts": {
    "outline": {"version": null, "path": null, "confirmation": null},
    "feishu": {"version": null, "url": null, "confirmation": null},
    "narration": {"version": null, "path": null, "confirmation": null},
    "srt": {"version": null, "path": null, "sha256": null, "confirmation": null}
  },
  "video_plan": {
    "mode": null,
    "audio": null,
    "burn_subtitles": null,
    "resolution": null,
    "asset_manifest": null,
    "cue_visual_map": null,
    "confirmation": null,
    "demo_range_ms": [0, 120000],
    "demo_is_preview_of_first_batch": true,
    "demo_file": null,
    "demo_confirmation": null
  },
  "batches": [],
  "next_start_ms": 0,
  "frozen_before_ms": null,
  "pending_user_decision": null
}
```

- 确认关联版本、时间、范围及一句简短依据，不保存整段聊天或凭据。
- 素材记录来源、用途、缺口与字幕ID对应；账号及访问令牌由安全连接管理。
- 每批记录主时间起止、文件、帧率帧数、SRT哈希、检查结果及确认。Demo是否并入首批写清，防止重复。
- 尚未确认的批次标记 `awaiting_confirmation`。收到“继续下一段”可视为当前批次接受，再只做下一批。
- 用户指出错误时记录变更，另出修正版；不能修改记录制造旧版已获通过的假象。
- 台词或SRT变更后标记受影响的下游版本；不重做冻结区段。
- 恢复时回读真实文档和文件。仅有路径或历史“完成”消息不足以证明成果有效。

阶段交付只说明具体成果和版本、需要确认什么、下一步是什么。视频再补主时间放置点及下一段接续点，不把状态字段、渲染日志或制作标注复制到画面。


实操替换另记 `practice`：预留主起止、录屏实际片长、视频帧数、局部SRT、主时间码SRT、后续偏移量和确认版本。全课最终成片与局部练习样片分别记录用途。视频批次同时保存整数起止帧，避免恢复时只凭舍入后的秒数续接。
