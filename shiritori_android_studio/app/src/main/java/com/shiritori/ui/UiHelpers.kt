package com.shiritori.ui

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.Drawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.view.Gravity
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.*

// ── Colour palette ────────────────────────────────────────────────────────────
val C_BG       = Color.parseColor("#07050F")
val C_CARD     = Color.parseColor("#0D0818")
val C_CARD2    = Color.parseColor("#130E24")
val C_BORDER   = Color.parseColor("#2D1B54")
val C_BORDER_A = Color.parseColor("#6D28D9")
val C_ACCENT   = Color.parseColor("#A855F7")
val C_GLOW     = Color.parseColor("#C084FC")
val C_RED      = Color.parseColor("#F472B6")
val C_RED_B    = Color.parseColor("#EC4899")
val C_GREEN    = Color.parseColor("#34D399")
val C_ORANGE   = Color.parseColor("#FB923C")
val C_DIM      = Color.parseColor("#5B4D7A")
val C_TEXT     = Color.parseColor("#EDE9FE")
val C_PURPLE   = Color.parseColor("#AB62FC")
val C_BTN_FILL = Color.parseColor("#4C1D95")
val C_GRAD_A   = Color.parseColor("#6D28D9")
val C_GRAD_B   = Color.parseColor("#A855F7")

// ── Dimension helpers ─────────────────────────────────────────────────────────
fun Int.dp(ctx: Context): Int = (this * ctx.resources.displayMetrics.density + 0.5f).toInt()

// ── Drawable factories ────────────────────────────────────────────────────────
fun roundedBg(fill: Int, stroke: Int = 0, strokeDp: Int = 0, radiusDp: Float = 16f, ctx: Context): GradientDrawable =
    GradientDrawable().apply {
        shape        = GradientDrawable.RECTANGLE
        cornerRadius = radiusDp * ctx.resources.displayMetrics.density
        setColor(fill)
        if (strokeDp > 0) setStroke(strokeDp.dp(ctx), stroke)
    }

fun gradBg(colorStart: Int, colorEnd: Int, radiusDp: Float = 28f, ctx: Context): GradientDrawable =
    GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(colorStart, colorEnd)).apply {
        cornerRadius = radiusDp * ctx.resources.displayMetrics.density
    }

// ── Ripple helper ─────────────────────────────────────────────────────────────
internal fun rippleWrap(base: Drawable, radiusDp: Float, ctx: Context): RippleDrawable {
    val mask = GradientDrawable().apply {
        shape        = GradientDrawable.RECTANGLE
        cornerRadius = radiusDp * ctx.resources.displayMetrics.density
        setColor(Color.WHITE)
    }
    return RippleDrawable(ColorStateList.valueOf(Color.argb(70, 200, 130, 252)), base, mask)
}

// ── Widget factories ──────────────────────────────────────────────────────────

fun Context.lp(
    w: Int = LinearLayout.LayoutParams.MATCH_PARENT,
    h: Int = LinearLayout.LayoutParams.WRAP_CONTENT,
    wt: Float = 0f,
    mb: Int = 0, mt: Int = 0
): LinearLayout.LayoutParams =
    LinearLayout.LayoutParams(w, h, wt).also {
        it.bottomMargin = mb.dp(this); it.topMargin = mt.dp(this)
    }

fun Context.lbl(
    text: String, sp: Float = 14f, color: Int = C_TEXT, bold: Boolean = false,
    gravity: Int = Gravity.START, wrap: Boolean = false
): TextView = TextView(this).apply {
    this.text = text; textSize = sp; setTextColor(color); this.gravity = gravity
    if (bold) setTypeface(null, Typeface.BOLD)
    letterSpacing = 0.02f
    layoutParams = lp(if (wrap) LinearLayout.LayoutParams.WRAP_CONTENT else LinearLayout.LayoutParams.MATCH_PARENT)
}

fun Context.bigLbl(text: String, sp: Float = 22f, color: Int = C_ACCENT): TextView =
    lbl(text, sp, color, bold = true, gravity = Gravity.CENTER).also {
        it.letterSpacing = 0.04f
        it.setShadowLayer(30f, 0f, 0f, Color.argb(150, 168, 85, 247))
    }

fun Context.space(dpVal: Int): View = View(this).apply {
    layoutParams = lp(h = dpVal.dp(this@space))
}

fun Context.divider(): View = View(this).apply {
    setBackgroundColor(Color.argb(60, 45, 27, 84))
    layoutParams = lp(h = 1.dp(this@divider), mb = 10, mt = 10)
}

fun Context.btnFilled(
    text: String, bgColor: Int = C_BTN_FILL, textColor: Int = C_TEXT,
    mb: Int = 10, onClick: () -> Unit
): Button = Button(this).apply {
    this.text = text; textSize = 14f; setTextColor(textColor); isAllCaps = false
    setTypeface(null, Typeface.BOLD)
    letterSpacing = 0.06f
    background = rippleWrap(gradBg(C_GRAD_A, C_GRAD_B, 28f, this@btnFilled), 28f, this@btnFilled)
    layoutParams = lp(h = 54.dp(this@btnFilled), mb = mb)
    stateListAnimator = null
    setPadding(20.dp(this@btnFilled), 0, 20.dp(this@btnFilled), 0)
    setOnClickListener { onClick() }
}

fun Context.btnOutline(
    text: String, borderColor: Int = C_ACCENT, textColor: Int = C_ACCENT,
    mb: Int = 10, onClick: () -> Unit
): Button = Button(this).apply {
    this.text = text; textSize = 14f; setTextColor(textColor); isAllCaps = false
    setTypeface(null, Typeface.BOLD)
    letterSpacing = 0.06f
    background = rippleWrap(roundedBg(Color.TRANSPARENT, borderColor, 2, 28f, this@btnOutline), 28f, this@btnOutline)
    layoutParams = lp(h = 54.dp(this@btnOutline), mb = mb)
    stateListAnimator = null
    setPadding(20.dp(this@btnOutline), 0, 20.dp(this@btnOutline), 0)
    setOnClickListener { onClick() }
}

fun Context.textIn(hint: String = "", h: Int = 52, onDone: (() -> Unit)? = null): EditText = EditText(this).apply {
    this.hint = hint; setHintTextColor(C_DIM); setTextColor(C_TEXT)
    textSize  = 14f
    background = roundedBg(C_CARD2, C_BORDER_A, 1, 14f, this@textIn)
    val p = 14.dp(this@textIn); setPadding(p, p / 2, p, p / 2)
    layoutParams = lp(h = h.dp(this@textIn), mb = 8)
    imeOptions  = EditorInfo.IME_ACTION_DONE
    setSingleLine()
    onDone?.let { fn -> setOnEditorActionListener { _, _, _ -> fn(); true } }
}

fun Context.card(borderColor: Int = C_BORDER, radiusDp: Float = 16f): LinearLayout =
    LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background  = roundedBg(C_CARD, borderColor, 1, radiusDp, this@card)
        val p = 16.dp(this@card); setPadding(p, p, p, p)
        layoutParams = lp(mb = 10)
    }

fun Context.scrollRoot(): Pair<ScrollView, LinearLayout> {
    val content = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        val p = 20.dp(this@scrollRoot)
        setPadding(p, p, p, (p * 1.5f).toInt())
        layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
    }
    val sv = ScrollView(this).apply {
        layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.MATCH_PARENT)
        isFillViewport = true
        setBackgroundColor(C_BG)
        addView(content)
    }
    return sv to content
}

fun Context.hRow(h: Int = 48, spacing: Int = 8): LinearLayout = LinearLayout(this).apply {
    orientation  = LinearLayout.HORIZONTAL
    layoutParams = lp(h = h.dp(this@hRow), mb = 6)
}

fun colorFor(name: String): Int = when (name) {
    "red"    -> C_RED_B
    "green"  -> C_GREEN
    "orange" -> C_ORANGE
    "accent" -> C_ACCENT
    "purple" -> C_PURPLE
    else     -> C_DIM
}
