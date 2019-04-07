package kundapanda.autisti.tiqr

import android.app.Activity
import android.content.Context
import android.content.Context.MODE_PRIVATE

enum class ThemeEnum {
    Dark, Light;

    /**
     * class for setting themes and switching based on enum
     */
    companion object {

        private fun toTheme(themeEnum: String): ThemeEnum {
            try {
                return valueOf(themeEnum)
            } catch (ex: Exception) {
            }
            return Dark

        }

        // keeping if necessary in the future
        fun setTheme(context: Context, theme: ThemeEnum) {
            val sp = context.getSharedPreferences("theme", MODE_PRIVATE)
            val editor = sp.edit()
            editor.putString("theme", theme.toString())
            editor.apply()
        }

        fun switchTheme(context: Context, activity: Activity) {
            val sp = context.getSharedPreferences("theme", MODE_PRIVATE)
            val currentTheme = sp.getString("theme", ThemeEnum.Dark.toString())
            if (currentTheme == ThemeEnum.Dark.toString()) {
                sp.edit().putString("theme", ThemeEnum.Light.toString()).apply()
            } else {
                sp.edit().putString("theme", ThemeEnum.Dark.toString()).apply()
            }
            activity.recreate()
        }

        fun getTheme(context: Context): ThemeEnum {
            val sp = context.getSharedPreferences("theme", MODE_PRIVATE)
            val theme = sp.getString("theme", ThemeEnum.Dark.toString())!!
            return ThemeEnum.toTheme(theme)
        }
    }

}
