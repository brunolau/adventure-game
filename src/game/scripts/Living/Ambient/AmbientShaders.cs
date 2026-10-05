using System;
using System.Collections.Generic;
using System.Text;
using Godot;

namespace LastBell.Game.Living.Ambient;

/// <summary>Effect of an ambient material.</summary>
public enum AmbientEffect
{
    /// <summary>Plain textured drawing.</summary>
    None,
    /// <summary>Wind sway of a cut-out (tree crowns, grass, curtains, washing lines).</summary>
    Sway,
    /// <summary>Water ripples and glints on a cut-out of the water surface.</summary>
    Water,
}

/// <summary>
/// Builds the canvas_item shaders of the ambient layers. Every variant can clip to a rect and/or a
/// mask texture placed on the canvas (alpha = where the layer may show, e.g. the sky above roofs,
/// the road between a hedge and a tram). Positions come from the layer node's local VERTEX, which is
/// the room canvas because ambient layers sit at the room origin. Time is a uniform fed by the layer,
/// so reduced motion can freeze it.
/// </summary>
public static class AmbientShaders
{
    private static readonly Dictionary<string, Shader> Cache = new(StringComparer.Ordinal);

    /// <summary>A (cached) shader for the feature combination.</summary>
    public static Shader Get(AmbientEffect effect, bool additive, bool clip, bool mask)
    {
        string key = $"{effect}|{additive}|{clip}|{mask}";
        if (Cache.TryGetValue(key, out var shader)) return shader;
        var code = new StringBuilder();
        code.AppendLine("shader_type canvas_item;");
        code.AppendLine(additive ? "render_mode blend_add;" : "render_mode blend_mix;");
        code.AppendLine("uniform float t = 0.0;");
        code.AppendLine("varying vec2 canvas_pos;");
        code.AppendLine("varying vec4 vertex_color;");
        if (clip) code.AppendLine("uniform vec4 clip_rect = vec4(0.0, 0.0, 1920.0, 1080.0);");
        if (mask)
        {
            code.AppendLine("uniform sampler2D mask_tex : filter_linear, repeat_disable;");
            code.AppendLine("uniform vec4 mask_rect = vec4(0.0, 0.0, 1920.0, 1080.0);");
            code.AppendLine("uniform bool mask_invert = false;");
        }
        if (effect == AmbientEffect.Sway)
        {
            code.AppendLine("""
                uniform vec2 tex_size = vec2(256.0);
                uniform float amp = 3.0;
                uniform float freq = 0.35;
                uniform float wavelength = 220.0;
                uniform float anchor = 1.0;
                uniform bool hang = false;
                uniform float flutter = 0.6;
                uniform float gust = 0.35;
                uniform float phase = 0.0;
                """);
        }
        if (effect == AmbientEffect.Water)
        {
            code.AppendLine("""
                uniform vec2 tex_size = vec2(256.0);
                uniform float amp = 1.5;
                uniform float speed = 1.0;
                uniform float glint = 0.35;
                uniform vec4 glint_color : source_color = vec4(1.0, 0.96, 0.85, 1.0);
                """);
        }
        code.AppendLine("void vertex() { canvas_pos = VERTEX; vertex_color = COLOR; }");
        code.AppendLine("void fragment() {");
        switch (effect)
        {
            case AmbientEffect.Sway:
                code.AppendLine("""
                    vec2 px = UV * tex_size;
                    float w = hang ? clamp((UV.y - anchor) / max(1.0 - anchor, 0.001), 0.0, 1.0)
                                   : clamp((anchor - UV.y) / max(anchor, 0.001), 0.0, 1.0);
                    w = w * w * (3.0 - 2.0 * w);
                    float tt = t * 6.2831853 * freq + phase;
                    float g = 1.0 - gust + gust * (0.5 + 0.5 * sin(tt * 0.23 + 1.7)) * (0.6 + 0.4 * sin(tt * 0.071));
                    float sx = sin(tt + px.x / wavelength * 2.4 + px.y / wavelength * 3.1)
                             + 0.55 * sin(tt * 1.73 + px.x / wavelength * 5.3 + 0.8);
                    float sy = 0.3 * sin(tt * 1.31 + px.x / wavelength * 4.1 + 2.0);
                    vec2 off = vec2(sx, sy) * amp * g * w;
                    off += vec2(sin(t * 7.3 + px.y * 0.21 + px.x * 0.05), cos(t * 6.1 + px.x * 0.17 + px.y * 0.03)) * flutter * w;
                    vec4 c = texture(TEXTURE, UV - off / tex_size);
                    """);
                break;
            case AmbientEffect.Water:
                code.AppendLine("""
                    vec2 px = UV * tex_size;
                    float tt = t * speed;
                    float ox = sin(px.y * 0.55 + tt * 1.9) * amp + sin(px.y * 1.3 - tt * 2.7 + px.x * 0.01) * amp * 0.5;
                    float oy = sin(px.x * 0.045 + tt * 1.2) * amp * 0.25;
                    vec4 c = texture(TEXTURE, UV + vec2(ox, oy) / tex_size);
                    float band = sin(px.y * 0.9 + sin(px.x * 0.013 + tt * 0.4) * 4.0 + tt * 0.8);
                    float sparkle = sin(px.x * 0.11 + tt * 1.7 + sin(px.y * 0.7) * 2.0) * sin(px.x * 0.037 - tt * 0.9 + px.y * 0.33);
                    float gl = smoothstep(0.82, 0.98, sparkle) * smoothstep(0.2, 0.9, band);
                    c.rgb = mix(c.rgb, glint_color.rgb, gl * glint * c.a);
                    """);
                break;
            default:
                code.AppendLine("vec4 c = texture(TEXTURE, UV);");
                break;
        }
        // In Godot 4 the fragment COLOR input is already texture * vertex colour; use the vertex colour only.
        code.AppendLine("c *= vertex_color;");
        if (clip)
            code.AppendLine("if (canvas_pos.x < clip_rect.x || canvas_pos.y < clip_rect.y || canvas_pos.x > clip_rect.x + clip_rect.z || canvas_pos.y > clip_rect.y + clip_rect.w) c.a = 0.0;");
        if (mask)
        {
            code.AppendLine("""
                vec2 muv = (canvas_pos - mask_rect.xy) / mask_rect.zw;
                float m = (muv.x < 0.0 || muv.y < 0.0 || muv.x > 1.0 || muv.y > 1.0) ? 0.0 : texture(mask_tex, muv).a;
                if (mask_invert) m = 1.0 - m;
                c.a *= m;
                """);
        }
        code.AppendLine("COLOR = c;");
        code.AppendLine("}");
        shader = new Shader { Code = code.ToString() };
        Cache[key] = shader;
        return shader;
    }
}
