<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" 
    encoding="utf-8" 
    indent="no" />   
<xsl:template match="/">
   <html>
      <head>
         <meta charset="utf-8"/>
         <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
      </head>
      <body>
         <xsl:attribute name="style">width=80%; margin: 0 auto;</xsl:attribute>
         <h2><xsl:attribute name="style">margin-bottom:60px;text-align:center;</xsl:attribute>
         <xsl:text>Беседа с </xsl:text><xsl:value-of select="//conversation/@friend"/></h2>
         <xsl:apply-templates/>
      </body>
   </html>
</xsl:template>

<xsl:template match="//message">
   <p>
   <xsl:attribute name="style">font-weight:bold;
   <xsl:choose>
      <xsl:when test="@direction='1'">color:#DC143C;</xsl:when>
      <xsl:when test="@direction='0'">color:#191970;</xsl:when>
   </xsl:choose>
   </xsl:attribute>
   <xsl:value-of select="@author"/><xsl:text> (</xsl:text><xsl:value-of select="@datetime"/><xsl:text>) </xsl:text>
   </p>
   <hr/>
   <xsl:if test='text() != ""'>   
      <xsl:call-template name="text" />
   </xsl:if>
   <xsl:apply-templates select="attachment"/> 
</xsl:template>


<xsl:template match="attachment">
   <p>
   <xsl:attribute name="style">font-weight:bolder;font-family: "Arial Narrow", Arial, sans-serif;</xsl:attribute>
   Вложение:</p>
   <xsl:choose>
      <xsl:when test="@type='audio'">
         <a>
         <xsl:attribute name="href"><xsl:value-of select="@url"/></xsl:attribute>
         <xsl:value-of select='@performer'/><xsl:text> - </xsl:text><xsl:value-of select='@title'/>
         </a>
         </xsl:when>
         <xsl:when test="@type='photo'">
         <a>
         <xsl:attribute name="href"><xsl:value-of select="@url"/></xsl:attribute>
         Изображение
         </a>
      </xsl:when>
      <xsl:when test="@type='video'">
         <xsl:call-template name="text" />
         <p><xsl:text>(</xsl:text>
         <a>
         <xsl:attribute name="href"><xsl:value-of select="@preview"/></xsl:attribute>
         Изображение-превью
         </a>
         <xsl:text>)</xsl:text></p>
         <p>
         <xsl:apply-templates select="description"/><xsl:text> (продолжительность </xsl:text><xsl:value-of select="@duration"/><xsl:text> c)</xsl:text>
         </p>
      </xsl:when>
      <xsl:when test="@type='doc'">
         <p><!--<xsl:value-of select="text()"/>--><xsl:call-template name="text" />
         <xsl:text> - </xsl:text>
         <a>
         <xsl:attribute name="href"><xsl:value-of select="@url"/></xsl:attribute>
         <xsl:text>документ </xsl:text><xsl:value-of select="@ext"/>
         </a><xsl:text>, </xsl:text><xsl:value-of select="@size"/>
         </p>
      </xsl:when>
      <xsl:when test="@type='wall'">
         <p>Запись со стены пользователя<xsl:text> </xsl:text><xsl:value-of select='@from'/>
         <xsl:if test='@owner'>
         взятая у <xsl:value-of select="@owner"/>
         </xsl:if><xsl:text> от </xsl:text><xsl:value-of select="@date"/></p>
         <p><xsl:call-template name="text" /></p>
         <xsl:if test="attachments">
         <p>
         <xsl:attribute name="style">font-size:xx-small;font-family:sans-serif;</xsl:attribute>
         У записи имеются собственные вложения, не показанные здесь.</p>
         </xsl:if>
      </xsl:when>
   </xsl:choose>
</xsl:template>

<xsl:template match="description">
   <xsl:call-template name="text" />
</xsl:template>   

<xsl:template name="text">
   <p>
   <xsl:attribute name="style">padding-left:20px;</xsl:attribute>
      <xsl:choose>
         <xsl:when test="not(contains(text(), '&#xA;'))">
            <xsl:value-of select="text()"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="substring-before(text(), '&#xA;')"/>
            <br/>
            <xsl:value-of select="substring-after(text(), '&#xA;')"/>
         </xsl:otherwise>
      </xsl:choose>
   </p>
</xsl:template>

</xsl:stylesheet>