
# Shader Generator

Submit-only: creates a backend generation job, returns `jobId`. Use the `track_progress` tool for job lifecycle after submission.

**Always use `generate.ts` for new shaders.** Manual authoring is only for editing existing asset code — never as a fallback when generation fails.

## Catalog-first rule — try existing assets before generation

Before generating a shader, call `browse_library` unless the user names an exact asset id that is already visible in `read_project`.

`browse_library` is the source of truth for built-in effects, built-in transitions, and project effect/transition assets. Built-ins are stable global asset ids, not per-project DB assets, so they may not appear in `read_project` asset lists.

Apply catalog entries with `edit_item`, do **not** call `submit_shader`.

Good catalog searches:

```text
browse_library(query: "zoom")
browse_library(category: "transitions", query: "dissolve")
browse_library(category: "audio-fx")
```

Generate only when no catalog entry matches the user's intent closely enough.

### `builtin:zoom` is track-bound only — DO NOT use item-bound

The default effect mode is `"item-bound"` (attach to a single item via `targetItemId`). **`builtin:zoom` does NOT render in item-bound mode** — the renderer reads zoom data exclusively from track-bound effect items. An item-bound zoom inserts into the DB silently but shows nothing in preview.

Use `mode: "track-bound"` with `trackId` + `trackBoundFrom` + `trackBoundDurationInFrames`. These three fields are required.

```text
# Zoom on the entire video clip
edit_item(json: '{"adds":[{"type":"effect","assetId":"builtin:zoom","mode":"track-bound","trackId":"<clip-trackId>","trackBoundFrom":<clip-fromFrame>,"trackBoundDurationInFrames":<clip-durationInFrames>,"propertyOverrides":{"magnification":1.5,"shape":"hold"}}]}')

# Zoom on a sub-range of the clip (e.g. frames 90–150 only, a punch zoom on a beat)
edit_item(json: '{"adds":[{"type":"effect","assetId":"builtin:zoom","mode":"track-bound","trackId":"<trackId>","trackBoundFrom":90,"trackBoundDurationInFrames":60,"propertyOverrides":{"magnification":2,"shape":"punch"}}]}')
```

Get `trackId` / `fromFrame` / `durationInFrames` from `read_project` (each video/image item lists its trackId and timeline-frame range).

| Key             | Type   | Range / values                             | Default | Notes                                          |
| --------------- | ------ | ------------------------------------------ | ------- | ---------------------------------------------- |
| `magnification` | number | 1–4                                        | `1.5`   | Zoom factor; 1 = no zoom, 2 = 2× in            |
| `focalPointX`   | number | 0–1                                        | `0.5`   | Horizontal focal point (0 = left, 1 = right)   |
| `focalPointY`   | number | 0–1                                        | `0.5`   | Vertical focal point (0 = top, 1 = bottom)     |
| `shape`         | select | `punch` / `hold` / `slow-push` / `instant` | `hold`  | Animation curve                                |
| `focalMode`     | select | `auto` / `manual`                          | `auto`  | `auto` picks subject; `manual` uses focalPoint |
| `easeInFrames`  | number | 0–60                                       | `8`     | Frames to ramp in                              |
| `easeOutFrames` | number | 0–60                                       | `8`     | Frames to ramp out                             |

Omit `propertyOverrides` entirely for default zoom. Send only the keys you want to change — patch semantics.

### Track-bound vs item-bound — the broader rule

Effect items in the schema have two modes:

- **`item-bound`** (default): `targetItemId` only. Effect covers the whole target item's playback. Works for shader effects, LUTs, color grades, blurs.
- **`track-bound`**: `trackId` + `trackBoundFrom` + `trackBoundDurationInFrames`. Effect covers a timeline range on a track, independent of any item. Required for `builtin:zoom`; also valid for any shader effect when you want it to cover a specific timeline range (e.g. a transition-like color shift across the boundary of two clips).

Default to item-bound for shader effects. Use track-bound when (a) the asset requires it (zoom), or (b) the effect should cover a timeline range that doesn't match a single item.

### Built-in LUT properties

```text
edit_item(json: '{"adds":[{"type":"effect","targetItemId":"<clip-id>","assetId":"builtin:slog3-s709","propertyOverrides":{"intensity":1}}]}')
```

| Key         | Type   | Range | Default | Notes                          |
| ----------- | ------ | ----- | ------- | ------------------------------ |
| `intensity` | number | 0–1   | `1`     | LUT strength; 1 = full applied |

To swap: delete the effect and re-add with a different `assetId`. To remove: delete the effect item.

These are separate from user-uploaded `.cube` LUT assets (see "Applying an Existing LUT Asset" below) — those use a different code path with `assetId:"lut"`.

## Beta Status Gate

New shader generation is beta. Before generating, warn the user and wait for explicit confirmation.

Use the user's language. Chinese: "新的特效/转场生成目前还是 beta 阶段，可能会有不稳定的问题。如果你坚持要做，我可以帮你实现。" Skip if user already acknowledged in the same request.

## Supported Targets

Effects and transitions apply to `video`, `image`, and `gif` items.

## Type Routing

Before generating anything, check two non-generation paths first:

1. **Catalog entry** — use `browse_library` for built-in and project effects/transitions.
2. **User-uploaded `.cube` LUT asset** that already exists in the project library — separate code path, see "Applying an Existing LUT Asset" below. The asset shows up in `read_project` with `type: lut`.

| User wants                                                           | `--type`     |
| -------------------------------------------------------------------- | ------------ |
| Video appearance (color, blur, glow, grain, distortion)              | `effect`     |
| Color grade / look (teal-orange, cinematic, vintage, LUT-style)      | `effect`     |
| Visibility control (mask, reveal, wipe, shape cutout, gradient fade) | `effect`     |
| Blend between clips (crossfade, dissolve, slide, 3D cube/page flip)  | `transition` |

"LUT-style" in the table means **generating a fresh GLSL color grade that resembles a LUT** — only when the user wants something new. If they want to apply a `.cube` file already in the library, don't generate; bind the existing asset instead.

No separate LUT or mask generator for the generation path — those are all `effect`.

## Applying an Existing LUT Asset

`.cube` files uploaded by the user become `lut` assets. Applying one to a clip is **not** generation — it's a single `edit_item` call that attaches an effect item whose `assetId` is the literal string `"lut"` and whose `propertyOverrides.lut` binds the real LUT asset id. (Legacy contract; the unified LUT API binds the LUT effect asset id directly — see `edit_item` description.)

```text
edit_item(json: '{"adds":[{"type":"effect","targetItemId":"<clip-id>","assetId":"lut","propertyOverrides":{"intensity":1,"lut":{"assetId":"<lut-asset-id>","assetType":"lut","type":"asset"}}}]}')
```

Key points:

- `assetId` is the literal string `"lut"`, not the LUT asset's id. The real LUT asset id goes inside `propertyOverrides.lut.assetId`.
- `intensity` is 0–1; default 1 (full strength).
- `targetItemType` defaults to `video`; also supports `image`, `gif`.
- To swap a LUT on an existing effect: update `propertyOverrides.lut.assetId` to the new LUT asset id.
- To remove: delete the effect item.

Do not call `generate.ts` for this path. Do not pass a real LUT asset id as `assetId` — the editor checks `assetId === "lut"` to route into the LUT renderer; passing a UUID silently renders nothing.

## Usage

Before calling `submit_shader`, restate the user's intent in one concrete sentence, then proceed immediately. After `track_progress` returns, state what was produced in one line — do NOT ask "要保留还是重新生成".

```ts
submit_shader({
  type: "effect",
  prompt: "Chromatic aberration with RGB split",
  name: "Chromatic Aberration",
});

submit_shader({
  type: "transition",
  prompt: "Smooth crossfade with soft edge",
  name: "Crossfade",
});

submit_shader({
  type: "effect",
  prompt: "Cinematic teal-orange color grade",
});

submit_shader({
  type: "effect",
  prompt: "Stronger version",
  referenceAssetIds: ["effect_asset_id"],
});
```

## Strategy

- Submit, then stop. Tell user the job was created.
- Use the `track_progress` tool for status/wait after submission.
- Generation always produces a library asset — never refuse because the timeline isn't ready.
- **Apply is separate and optional.** Only apply when user explicitly asks ("加到视频", "apply", "用到第一段"). When ambiguous, default to library-only.

## Editing Existing Properties

Any time you're about to edit shader `asset.properties`, applied effect/transition `item.propertyOverrides`, or promote a hardcoded shader value, read [`references/property-changes.md`](references/property-changes.md) first.

It reinforces that shader `properties` is an array, but the allowed shader property types are only `number`, `boolean`, `color`, `select`, and `vec2`. Motion Graphic properties are also arrays, but use a different type set.

## Parameters

| Param               | Description                                                                                                                                                    | Default |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `type`              | `"effect"` or `"transition"` (req'd)                                                                                                                           | —       |
| `prompt`            | Description of the shader (req'd)                                                                                                                              | —       |
| `name`              | Asset name shown in library                                                                                                                                    | —       |
| `referenceAssetIds` | Asset ids. Image id → model LOOKS AT it for visual inspiration. Effect/transition id → reuse its code as style anchor (≤1 per submit, kind must match `type`). | —       |

## Output

Returns `{ success, job: { jobId, status }, manage: { status, wait, watch } }`.

## Applying to Timeline

Only when user explicitly requests. Call `read_project` first for fresh timeline state.

### Effect

```text
edit_item(json: '{"adds":[{"type":"effect","targetItemId":"<id>","assetId":"<id>","enabled":true,"propertyOverrides":{}}]}')
```

### Transition

Requires two adjacent same-track endpoints. `edit_item` validates live seam feasibility and refuses durations that would require freeze frames or overlapping neighboring transitions. If the add fails, retry with the suggested `durationInFrames`, trim the clips to expose handles, delete/shorten neighboring transitions, or keep a hard cut.

```text
edit_item(json: '{"adds":[{"type":"transition","assetId":"<id>","outgoingItemId":"<id1>","incomingItemId":"<id2>","durationInFrames":30}]}')
```

## Validation & Verification

### Backend Validation

When generating via `generate.ts`, the backend handles validation automatically (transpile, AST security, class structure, retry on failure).

### Manual Code Verification

**NEVER write shader code from scratch.** Always use `generate.ts` for new shaders. This section is ONLY for modifying existing shader code that was already generated.

When writing shader code manually, read `@references/design-principles.md` first. If the change touches editable properties, also read `@references/property-changes.md`.

Typical workflow:

1. `read_project` with the shader `assetId` and `code: true` — read the current source.
2. Edit the source in your own context.
3. `edit_asset` with `action=update`, the same `assetId`, and the full replacement source inline in `json.code`. Validation runs automatically on update — if code is invalid, the update is rejected with error details.


---

## 附：cube-rotate

---
tags: 3d, cube, rotate, box, spin
description: 3D cube rotation — outgoing on front face, incoming on right face, rotates 90° around Y axis.
complexity: high
---

# Cube Rotate Transition

Uses BoxGeometry with per-face materials. Only two faces carry textures (front=outgoing, right=incoming), the rest are black.

Key decisions:

- `BoxGeometry(1.5 * aspect, 1.5, 1.5 * aspect)` — depth matches width so the cube face is square in the X/Z plane, preserving correct rotation geometry regardless of video aspect ratio.
- `camera.position.z = 2.5` — positions the camera so the cube face fills most of the viewport at FOV 45.
- Rotation is around Y axis with cubic easing — starts slow, accelerates mid-turn, decelerates at the end.

```typescript
class CubeTransition extends TransitionProcessor {
  private scene!: Scene;
  private camera!: PerspectiveCamera;
  private cube!: Mesh;
  private outMat!: MeshBasicMaterial;
  private inMat!: MeshBasicMaterial;

  async initialize(ctx: TransitionInitContext): Promise<void> {
    const aspect = ctx.width / ctx.height;
    this.scene = new Scene();
    this.camera = new PerspectiveCamera(45, aspect, 0.1, 1000);
    this.camera.position.z = 2.5;

    const geometry = new BoxGeometry(1.5 * aspect, 1.5, 1.5 * aspect);
    this.outMat = new MeshBasicMaterial();
    this.inMat = new MeshBasicMaterial();

    // Front face (index 4) and Right face (index 0)
    const materials = [
      this.inMat,
      new MeshBasicMaterial({ color: 0x000000 }),
      new MeshBasicMaterial({ color: 0x000000 }),
      new MeshBasicMaterial({ color: 0x000000 }),
      this.outMat,
      new MeshBasicMaterial({ color: 0x000000 }),
    ];
    this.cube = new Mesh(geometry, materials);
    this.scene.add(this.cube);
  }

  protected render(ctx: TransitionRenderContext): WebGLTexture {
    this.outMat.map = ctx.three.wrapTexture(ctx.outgoingTexture);
    this.inMat.map = ctx.three.wrapTexture(ctx.incomingTexture);

    // Cubic easing
    const p = ctx.progress;
    const eased = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
    this.cube.rotation.y = -eased * (Math.PI / 2);

    return ctx.threePass(this.scene, this.camera);
  }
}
```


---

## 附：door-open

---
tags: 3d, door, open, split, swing, hinge
description: Door open transition — outgoing splits into two halves that swing open like doors, revealing incoming behind.
complexity: high
---

# Door Open Transition

Three layers: incoming backdrop behind, left door and right door in front. Each door shows the correct half of the outgoing texture and swings outward on its outer edge hinge.

Key decisions:

- **Camera distance from FOV**: `dist = 1 / Math.tan(fovRad / 2)` ensures height=2 plane fills viewport. No hardcoded camera z.
- **UV remapping for split texture**: Left door UVs remapped to u:[0, 0.5], right door to u:[0.5, 1]. Each half-panel shows only its corresponding half of the outgoing frame — not the full frame squeezed.
- **Object3D pivot pattern**: Each door's geometry is offset so the hinge edge sits at local origin. The Object3D parent is positioned at the screen edge. Rotating the Object3D swings the door around the correct hinge. Left hinge at x=-W/2, right hinge at x=+W/2.
- **Doors swing into screen**: Left door rotates -Y (swings away-left), right door rotates +Y (swings away-right). Both swing toward negative z, creating a natural "opening toward the viewer" perspective effect.

```typescript
class DoorOpenTransition extends TransitionProcessor {
  private scene!: Scene;
  private camera!: PerspectiveCamera;
  private leftPivot!: Object3D;
  private rightPivot!: Object3D;
  private leftMat!: MeshBasicMaterial;
  private rightMat!: MeshBasicMaterial;
  private backMat!: MeshBasicMaterial;

  async initialize(ctx: TransitionInitContext): Promise<void> {
    const aspect = ctx.width / ctx.height;
    const fov = 50;
    const dist = 1 / Math.tan((fov * Math.PI) / 180 / 2);

    this.scene = new Scene();
    this.camera = new PerspectiveCamera(fov, aspect, 0.01, 100);
    this.camera.position.z = dist;

    const W = 2 * aspect;
    const H = 2;

    // Backdrop: incoming clip, full width
    this.backMat = new MeshBasicMaterial({ side: 2 });
    const back = new Mesh(new PlaneGeometry(W, H), this.backMat);
    back.position.z = -0.05;
    this.scene.add(back);

    // Left door: shows LEFT half of outgoing (UV u: 0→0.5)
    // Hinge at LEFT edge (x = -W/2)
    const leftGeo = new PlaneGeometry(W / 2, H, 1, 1);
    const leftUV = leftGeo.attributes.uv;
    for (let i = 0; i < leftUV.count; i++) {
      leftUV.setX(i, leftUV.getX(i) * 0.5);
    }
    leftUV.needsUpdate = true;
    this.leftMat = new MeshBasicMaterial({ side: 2 });
    const leftDoor = new Mesh(leftGeo, this.leftMat);
    // Shift geometry so LEFT edge is at local origin (pivot)
    leftDoor.geometry.translate(W / 4, 0, 0);
    this.leftPivot = new Object3D();
    this.leftPivot.position.x = -W / 2;
    this.leftPivot.add(leftDoor);
    this.scene.add(this.leftPivot);

    // Right door: shows RIGHT half of outgoing (UV u: 0.5→1)
    // Hinge at RIGHT edge (x = +W/2)
    const rightGeo = new PlaneGeometry(W / 2, H, 1, 1);
    const rightUV = rightGeo.attributes.uv;
    for (let i = 0; i < rightUV.count; i++) {
      rightUV.setX(i, 0.5 + rightUV.getX(i) * 0.5);
    }
    rightUV.needsUpdate = true;
    this.rightMat = new MeshBasicMaterial({ side: 2 });
    const rightDoor = new Mesh(rightGeo, this.rightMat);
    // Shift geometry so RIGHT edge is at local origin (pivot)
    rightDoor.geometry.translate(-W / 4, 0, 0);
    this.rightPivot = new Object3D();
    this.rightPivot.position.x = W / 2;
    this.rightPivot.add(rightDoor);
    this.scene.add(this.rightPivot);
  }

  protected render(ctx: TransitionRenderContext): WebGLTexture {
    const p = ctx.progress;
    const eased = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;

    this.backMat.map = ctx.three.wrapTexture(ctx.incomingTexture);
    this.leftMat.map = ctx.three.wrapTexture(ctx.outgoingTexture);
    this.rightMat.map = ctx.three.wrapTexture(ctx.outgoingTexture);

    // Left door: hinge on left, swings into screen (negative Y rotation)
    this.leftPivot.rotation.y = -eased * (Math.PI / 2);
    // Right door: hinge on right, swings into screen (positive Y rotation)
    this.rightPivot.rotation.y = eased * (Math.PI / 2);

    return ctx.threePass(this.scene, this.camera);
  }
}
```


---

## 附：page-curl

---
tags: 3d, page, curl, flip, turn, book, peel
description: Page curl transition — outgoing page curls away from left to right, revealing incoming underneath.
complexity: high
---

# Page Curl Transition

Two-layer approach: incoming page sits flat behind (z=-0.001), outgoing page is a high-res subdivided plane (80x80) whose vertices are deformed each frame to simulate a cylindrical curl.

Key decisions:

- **Camera distance from FOV**: `dist = 1 / Math.tan(fovRad / 2)` ensures the plane (height=2) exactly fills the viewport vertically. No hardcoded camera z.
- **Radius proportional to page width**: `radius = W * 0.08` scales with aspect ratio, preventing the curl from being too tight on wide videos or too loose on tall ones.
- **Fold sweeps left→right**: `foldX = -W/2 + eased * (W + radius * PI)`. At progress=0 fold is at left edge (nothing curled), at progress=1 it's past the right edge (fully curled away).
- **UV-based position reconstruction**: Original positions are derived from UVs each frame (`ox = uv.getX(i) * W - W/2`), since the position buffer gets overwritten. UVs are immutable.
- **Three curl zones**: (1) `ox <= foldX` → flat, not yet reached. (2) `ox > foldX, angle <= PI` → wrapping around cylinder. (3) `angle > PI` → past 180°, extends flat at z=2\*radius back toward -x (folded-back page visible on top).
- **`side: 2` (DoubleSide)**: Back of the curling page is visible during the curl.
- **Texture swap**: `incomingMat` gets `outgoingTexture`, `curlMat` gets `incomingTexture` — the curling-away page shows incoming, the flat base shows outgoing. This creates the effect of a new page being revealed as the old one peels off.

```typescript
export class PageCurlTransition extends TransitionProcessor {
  private scene!: Scene;
  private camera!: PerspectiveCamera;
  private curlMesh!: Mesh;
  private incomingMesh!: Mesh;
  private curlMat!: MeshBasicMaterial;
  private incomingMat!: MeshBasicMaterial;
  private aspect!: number;
  private W!: number;

  async initialize(ctx: TransitionInitContext): Promise<void> {
    this.aspect = ctx.width / ctx.height;
    this.scene = new Scene();

    const fov = 45;
    const fovRad = (fov * Math.PI) / 180;
    const dist = 1 / Math.tan(fovRad / 2);

    this.camera = new PerspectiveCamera(fov, this.aspect, 0.01, 100);
    this.camera.position.z = dist;

    this.W = 2 * this.aspect;
    const H = 2;

    this.incomingMat = new MeshBasicMaterial({ side: 2 });
    this.incomingMesh = new Mesh(
      new PlaneGeometry(this.W, H),
      this.incomingMat,
    );
    this.incomingMesh.position.z = -0.001;
    this.scene.add(this.incomingMesh);

    this.curlMat = new MeshBasicMaterial({ side: 2 });
    this.curlMesh = new Mesh(
      new PlaneGeometry(this.W, H, 80, 80),
      this.curlMat,
    );
    this.scene.add(this.curlMesh);
  }

  protected render(ctx: TransitionRenderContext): WebGLTexture {
    const p = ctx.progress;
    const eased = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;

    this.incomingMat.map = ctx.three.wrapTexture(ctx.outgoingTexture);
    this.curlMat.map = ctx.three.wrapTexture(ctx.incomingTexture);

    const W = this.W;
    const radius = W * 0.08;
    const foldX = -W / 2 + eased * (W + radius * Math.PI);

    const pos = this.curlMesh.geometry.attributes.position;
    const uv = this.curlMesh.geometry.attributes.uv;
    const count = pos.count;

    for (let i = 0; i < count; i++) {
      const ox = uv.getX(i) * W - W / 2;
      const oy = uv.getY(i) * 2 - 1;

      let nx: number, nz: number;

      if (ox <= foldX) {
        nx = ox;
        nz = 0;
      } else {
        const delta = ox - foldX;
        const angle = delta / radius;
        if (angle <= Math.PI) {
          nx = foldX + radius * Math.sin(angle);
          nz = radius * (1 - Math.cos(angle));
        } else {
          const extra = delta - radius * Math.PI;
          nx = foldX - extra;
          nz = radius * 2;
        }
      }

      pos.setXYZ(i, nx, oy, nz);
    }

    pos.needsUpdate = true;
    this.curlMesh.geometry.computeVertexNormals();

    return ctx.threePass(this.scene, this.camera);
  }
}
```


---

## 附：design-principles

# Shader Effect & Transition Design Principles

This document contains the system prompt and design guidelines used by Gemini when generating shader code. Follow these same rules when writing shader code manually.

<role>
You are an expert WebGL shader programmer writing GPU-accelerated video effects and transitions for a professional video editor.
You write TypeScript classes that extend EffectProcessor (effects) or TransitionProcessor (transitions).
</role>

## Constraints

**Violations cause runtime crashes. Strict compliance required.**

1. **TypeScript only.** Class MUST extend `EffectProcessor` (effect) or `TransitionProcessor` (transition).
2. **No import statements.** `EffectProcessor` / `TransitionProcessor` are pre-injected in scope.
3. **Use `export` before class declaration** (it will be stripped automatically).
4. **Fragment shaders MUST use `#version 300 es`, `precision highp float`.**
5. **Available in scope:** EffectProcessor, TransitionProcessor, Array, Object, Math, Float32Array, Int32Array, Uint8Array, console.
6. **BLOCKED (will fail validation):** window, document, fetch, eval, Function, import, require, setTimeout, setInterval, process, globalThis, crypto, WebSocket, XMLHttpRequest, navigator, localStorage, sessionStorage, Worker, ServiceWorker, and all other browser/Node globals.
7. **Max code length:** 50,000 characters.
8. **Multi-pass effects:** Always call `ctx.releaseTexture()` on intermediate textures to avoid GPU memory leaks.
9. **Do NOT implement `getMetadata()`.** Properties are declared in the JSON response, not in code.
10. **Shader compilation:** All shaders MUST be compiled in `initialize(ctx)` via `ctx.compileShader({ id, fragmentShader, vertexShader? })`. The `id` must match the `id` used in `renderPass()`.
11. **Custom vertex shader:** Pass a custom vertex shader in `compileShader({ id, fragmentShader, vertexShader })`. If omitted, the default vertex shader is used.

## Effect API

The default vertex shader provides `v_texCoord` (vec2, 0-1 UV coordinates). Use `uniform sampler2D u_input` for the input video texture.

```typescript
interface EffectRenderContext {
  readonly gl: WebGL2RenderingContext;
  readonly width: number;
  readonly height: number;
  readonly frame: number;
  readonly time: number;
  readonly fps: number;
  readonly progress: number; // 0-1 progress within clip
  readonly inputTexture: WebGLTexture;
  readonly properties: Record<string, unknown> | undefined;
  renderPass(options: RenderPassOptions): WebGLTexture;
  acquireTexture(): WebGLTexture;
  releaseTexture(texture: WebGLTexture): void;
}

interface EffectInitContext {
  compileShader(options: {
    id: string;
    fragmentShader: string;
    vertexShader?: string;
  }): void;
  readonly width: number;
  readonly height: number;
}
```

### Effect Example

```typescript
export class GrayscaleEffect extends EffectProcessor {
  async initialize(ctx: EffectInitContext): Promise<void> {
    ctx.compileShader({
      id: "grayscale",
      fragmentShader: `#version 300 es
      precision highp float;
      uniform sampler2D u_input;
      uniform float u_intensity;
      in vec2 v_texCoord;
      out vec4 fragColor;
      void main() {
        vec4 color = texture(u_input, v_texCoord);
        float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
        fragColor = vec4(mix(color.rgb, vec3(gray), u_intensity), color.a);
      }`,
    });
  }

  protected render(ctx: EffectRenderContext): WebGLTexture {
    const props = ctx.properties as { intensity?: number } | undefined;
    return ctx.renderPass({
      id: "grayscale",
      textures: { u_input: ctx.inputTexture },
      uniforms: { u_intensity: props?.intensity ?? 1.0 },
    });
  }
}
```

## Transition API

A transition blends TWO video frames: the outgoing clip (fading out) and the incoming clip (fading in).
The shader receives both textures and a `progress` value (0→1). At progress=0, show only the outgoing clip. At progress=1, show only the incoming clip.

Use `uniform sampler2D u_outgoing` and `uniform sampler2D u_incoming` for the two video textures. Use `uniform float u_progress` for the blend progress.

```typescript
interface TransitionRenderContext {
  readonly gl: WebGL2RenderingContext;
  readonly width: number;
  readonly height: number;
  readonly frame: number;
  readonly time: number;
  readonly fps: number;
  readonly progress: number; // 0→1 (0=outgoing, 1=incoming)
  readonly outgoingTexture: WebGLTexture;
  readonly incomingTexture: WebGLTexture;
  readonly properties: Record<string, unknown> | undefined;
  renderPass(options: RenderPassOptions): WebGLTexture;
  acquireTexture(): WebGLTexture;
  releaseTexture(texture: WebGLTexture): void;
}

interface TransitionInitContext {
  compileShader(options: {
    id: string;
    fragmentShader: string;
    vertexShader?: string;
  }): void;
  readonly width: number;
  readonly height: number;
}
```

### Transition Examples

**Crossfade:**

```typescript
export class CrossfadeTransition extends TransitionProcessor {
  async initialize(ctx: TransitionInitContext): Promise<void> {
    ctx.compileShader({
      id: "crossfade",
      fragmentShader: `#version 300 es
      precision highp float;
      uniform sampler2D u_outgoing;
      uniform sampler2D u_incoming;
      uniform float u_progress;
      in vec2 v_texCoord;
      out vec4 fragColor;
      void main() {
        vec4 outColor = texture(u_outgoing, v_texCoord);
        vec4 inColor = texture(u_incoming, v_texCoord);
        fragColor = mix(outColor, inColor, u_progress);
      }`,
    });
  }

  protected render(ctx: TransitionRenderContext): WebGLTexture {
    return ctx.renderPass({
      id: "crossfade",
      textures: {
        u_outgoing: ctx.outgoingTexture,
        u_incoming: ctx.incomingTexture,
      },
      uniforms: { u_progress: ctx.progress },
    });
  }
}
```

**Directional Wipe:**

```typescript
export class DirectionalWipe extends TransitionProcessor {
  async initialize(ctx: TransitionInitContext): Promise<void> {
    ctx.compileShader({
      id: "wipe",
      fragmentShader: `#version 300 es
      precision highp float;
      uniform sampler2D u_outgoing;
      uniform sampler2D u_incoming;
      uniform float u_progress;
      uniform float u_softness;
      uniform int u_direction;
      in vec2 v_texCoord;
      out vec4 fragColor;
      void main() {
        float coord = u_direction == 0 ? v_texCoord.x :
                      u_direction == 1 ? 1.0 - v_texCoord.x :
                      u_direction == 2 ? v_texCoord.y : 1.0 - v_texCoord.y;
        float edge = smoothstep(u_progress - u_softness, u_progress + u_softness, coord);
        vec4 outColor = texture(u_outgoing, v_texCoord);
        vec4 inColor = texture(u_incoming, v_texCoord);
        fragColor = mix(inColor, outColor, edge);
      }`,
    });
  }

  protected render(ctx: TransitionRenderContext): WebGLTexture {
    const props = ctx.properties as
      | { softness?: number; direction?: string }
      | undefined;
    const dirMap: Record<string, number> = {
      left: 0,
      right: 1,
      top: 2,
      bottom: 3,
    };
    return ctx.renderPass({
      id: "wipe",
      textures: {
        u_outgoing: ctx.outgoingTexture,
        u_incoming: ctx.incomingTexture,
      },
      uniforms: {
        u_progress: ctx.progress,
        u_softness: props?.softness ?? 0.1,
        u_direction: dirMap[props?.direction ?? "left"] ?? 0,
      },
    });
  }
}
```

## Properties

Properties define UI controls exposed to the user. Declare them in the JSON output, NOT in `getMetadata()`.

Shader `properties` is always an array. Each entry: `{ key, label, type, defaultValue, [min, max, step] }`.

Shader property types are: `number`, `boolean`, `color`, `select`, `vec2`. Motion Graphic properties are also arrays, but use a different type set — do not use Motion Graphic-only types such as `text`, `font`, `image`, or `video` for shaders.

| Type      | Use case                    | defaultValue example |
| --------- | --------------------------- | -------------------- |
| `number`  | Intensity, radius, softness | `"0.5"`              |
| `boolean` | Toggle on/off               | `"true"`             |
| `color`   | Tint color                  | `"#ffffff"`          |
| `select`  | Direction, mode choice      | `"left"`             |
| `vec2`    | Center point, offset        | `"0.5,0.5"`          |

Number properties render as sliders when `min` and `max` are present; `step` is optional.

## Design Principles

**1. Subtle Over Heavy**
Effects should enhance, not overpower. Default property values should produce a tasteful result out of the box — users should be impressed on first apply, not scrambling to dial it down.

**1a. Broadcast-Quality Aesthetics (Effects)**
Design for a professional video editor, not a toy filter app.

- Think film color grading (Davinci Resolve), not Instagram sticker filters. Subtle warmth shift > heavy neon overlay.
- When manipulating color, preserve skin tones and natural contrast. Crushing blacks or blowing highlights screams amateur.
- Animated effects should use smooth easing (sine, exponential decay), not linear ramps. Match frequency to the real-world phenomenon (grain flickers fast, lens flares drift slow).
- Overlay elements (particles, bokeh, light leaks) must use `additive` or `screen` blending — never paste opaque shapes.
- Multi-pass blur/glow needs enough taps for smooth gradients (5+ or two-pass separable Gaussian).
- Avoid: solid color overlays as "tint", single-pixel blur as "cinematic", uniform noise as "film grain", constant-offset chromatic aberration (real CA is radial).

**2. Performance Matters**

- Minimize texture samples and passes. One pass is ideal; two is acceptable; three+ needs justification.
- Avoid branching in fragment shaders when possible (use `mix`, `step`, `smoothstep`).
- Use `mediump` for values that don't need full precision (e.g. UV coordinates in simple effects).

**3. Smooth Transitions**
Transitions must be visually seamless: at `progress=0` the output must be pixel-identical to the outgoing clip, at `progress=1` pixel-identical to the incoming clip. No sudden jumps, no artifacts at the boundary frames.

**3a. Cinematic Motion (Transitions)**
Design for a professional video editor, not PowerPoint.

- NEVER use linear progress. Always apply easing — cubic (`p*p*p`), exponential (`pow(p, 2.5)`), ease-in-out (`smoothstep`), or spring-like curves.
- Add secondary motion: if geometry moves, add rotation or scale. If a wipe reveals, add a soft glow or blur at the edge.
- Stagger timing across elements — simultaneous motion looks robotic.
- Add depth cues: shadows, parallax, perspective distortion, blur on receding elements.
- Both clips should participate in the transition. A static incoming frame behind a moving outgoing frame is lazy.
- For 3D: ramp lighting intensity with progress so the first frame matches the source video exactly. Only apply strong specular/phong shading after motion begins.
- Avoid flat 2D slides with hard edges, uniform-speed grid dissolves, and unlit 3D rotations.

**4. Expose the Right Controls**

- Every effect should expose an `intensity` or `amount` property (0-1) so the user can dial it back.
- Transitions should expose `softness` / `feather` where applicable.
- Keep property count low (2-5). Too many controls overwhelm the user.

**5. GPU Memory Hygiene**
Multi-pass effects must release intermediate textures via `ctx.releaseTexture()`. Leaking textures causes GPU memory exhaustion during long playback.

**6. Aspect Ratio in 3D Transitions**
3D transitions using `threePass()` must account for the video aspect ratio. In `initialize(ctx)`, use `const aspect = ctx.width / ctx.height` to create correctly-sized geometry: `PlaneGeometry(2 * aspect, 2)` — never `PlaneGeometry(2, 2)`. Derive face positions and camera distance from `aspect` and the camera's FOV so the outgoing frame fills the viewport exactly at `progress=0`. Hard-coded geometry positions (e.g. `z = 1`) produce distorted or letterboxed output on non-square videos.

## Output Format

Respond with valid JSON:

```json
{
  "typescript_code": "export class ... extends EffectProcessor { ... }",
  "name": "Short effect name",
  "description": "Brief description of what the effect does",
  "properties": [
    {
      "key": "intensity",
      "label": "Intensity",
      "type": "number",
      "defaultValue": "1.0",
      "min": 0,
      "max": 1,
      "step": 0.01
    }
  ]
}
```


---

## 附：property-changes

# Shader Property Changes

Read this whenever a task touches editable shader properties: adding, renaming, or removing a property key; changing a default; promoting a hardcoded shader constant; or updating one applied effect/transition override.

## Data Model

Three layers, in strict order:

1. `asset.properties` - editable property **schema** on the effect or transition asset. Declares every key (type, label, default, and `min`/`max`/`step` or `options`). Source of truth.
2. `item.propertyOverrides` - per-applied-item overrides. Sparse: only values that differ for that specific effect/transition item need to be stored.
3. `ctx.properties` - runtime object passed into the shader processor. Built by merging schema defaults with the applied item's overrides.

Shader property types are: `number`, `boolean`, `color`, `select`, `vec2`. Motion Graphic properties are also arrays, but use a different type set - do not use Motion Graphic-only types such as `text`, `font`, `image`, or `video` for shaders.

**Prerequisite rule:** a key must exist in `asset.properties` before shader code should read `ctx.properties.key`, and before an applied item override can show a control for that key.

For shader assets, `asset.properties` is always an array. Each object inside the array is one editable property entry.

## Decision Table

Use `edit_asset` when:

- shader code starts reading a new `ctx.properties.key`
- a property key is added, renamed, or removed
- a property type, label, options, or default changes

Use an applied item update with `propertyOverrides` when:

- the key already exists on the effect/transition asset
- one applied effect/transition item should use a different value than the asset default

Do not use `propertyOverrides` to add schema. Do not use `edit_asset` for one-off instance values.

## Promoting Hardcoded Values to Properties

When the user asks to adjust a hardcoded shader value (intensity, radius, color, softness, direction, center point, or anything tweakable), in the same turn both make the shader change AND promote the value to a property. That way they can self-serve next time from the editor's property controls.

Skip promotion when:

- user explicitly frames it as one-off ("just this once", "only for this item")
- the value is structural: texture binding names, pass IDs, GLSL constants required for loop unrolling, or math tied to shader correctness
- the asset is a locked template the user doesn't own

Workflow (one turn):

1. Fetch the current shader asset code and properties
2. Locate the hardcoded literal
3. Replace it with `ctx.properties.<key>` plus a fallback to the current value so existing items render identically
4. Add a matching entry inside the `properties` array with sensible `min`/`max`/`step` or `options`
5. `edit_asset` with both the updated `code` and `properties` in one call
6. If the user also asked for a specific new value, apply it either as the new `defaultValue` (baseline) or as a `propertyOverride` on the specific applied item

Example - promoting an intensity constant:

```ts
const props = ctx.properties as { intensity?: number } | undefined;
const intensity = props?.intensity ?? 0.6;
```

```json
"properties": [
  {
    "key": "intensity",
    "label": "Intensity",
    "type": "number",
    "defaultValue": 0.6,
    "min": 0,
    "max": 1,
    "step": 0.01
  }
]
```

Example - promoting a center point:

```json
"properties": [
  {
    "key": "center",
    "label": "Center",
    "type": "vec2",
    "defaultValue": [0.5, 0.5]
  }
]
```

## Asset-Level Changes

When the schema changes, update the shader asset's `code` and `properties` in the same `edit_asset` call. Validation runs on update and rejects unsupported property shapes or shader-only/Motion-Graphic-only type mixups.

1. Fetch the current asset with code and properties
2. Update code to read the target key from `ctx.properties`
3. `edit_asset` with both the new `properties` array and the new `code`
4. If a key was renamed, migrate affected applied item overrides to the new key

Keep keys stable when possible - renames create migration work.

## Item-Level Changes

Prerequisite: the key must already exist on `asset.properties`. If it doesn't, do not update `propertyOverrides` - go to "Promoting Hardcoded Values" or "Asset-Level Changes" first.

Update only the applied effect/transition item whose value should differ from the asset default.

```json
{ "propertyOverrides": { "intensity": 0.8 } }
```

```json
{ "propertyOverrides": { "center": [0.45, 0.55] } }
```
