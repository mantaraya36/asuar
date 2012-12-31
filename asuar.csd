<CsoundSynthesizer>
<CsOptions>
-odac -+rtaudio=alsa -+rtmidi=alsa -Ma
-B4096 -b2048 -d --logfile=null
</CsOptions>
<CsInstruments>

sr = 22050
ksmps = 1024
nchnls = 1
0dbfs = 1.0

gasigL init 0
gasigR init 0
gaRM1L init 0
gaRM1R init 0
gaRM2L init 0
gaRM2R init 0

maxalloc 2, 10
massign 1,2

chn_k "lfo1shape", 1
chn_k "lfo1amt", 1
chn_k "lfo1freq", 1
chn_k "lfo1patch", 1
chn_k "lfo1dest", 1
chn_k "lfo2shape", 1
chn_k "lfo2amt", 1
chn_k "lfo2freq", 1
chn_k "lfo2patch", 1
chn_k "lfo2dest", 1
chn_k "att", 1
chn_k "dec", 1
chn_k "sus", 1
chn_k "rel", 1
chn_k "fatt", 1
chn_k "fdec", 1
chn_k "fsus", 1
chn_k "frel", 1
chn_k "fenvamount", 1
chn_k "cf", 1
chn_k "res", 1
chn_k "pan", 1
chn_k "out", 1
chn_k "rm1", 1
chn_k "rm2", 1
chn_k "rm1amount", 1
chn_k "rm1rate", 1
chn_k "rm1torm2", 1
chn_k "rm2amount", 1
chn_k "rm2rate", 1
chn_k "outlevel", 1
chn_k "revmix", 1
chn_k "Roomsize", 1
chn_k "HFDamp", 1

turnon 1 ; 2 LFOs
turnon 80 ; RM 1
turnon 81 ; RM 2
turnon 99 ; reverb

gisine ftgen 0,0, 4096, 10, 1


instr 1  ; lfos
; TODO make shape dynamic!
ilfo1shape chnget "lfo1shape"
klfo1amt chnget "lfo1amt"
klfo1freq chnget "lfo1freq"

galfo1 lfo klfo1amt, klfo1freq, ilfo1shape

ilfo2shape chnget "lfo2shape"
klfo2amt chnget "lfo2amt"
klfo2freq chnget "lfo2freq"

galfo2 lfo klfo2amt, klfo2freq, ilfo2shape

;asig oscils 0.2, 440, 0
;outch 1, asig
endin

instr 2 ;square wave generators

iatt chnget "att"
idec chnget "dec"
isus chnget "sus"
irel chnget "rel"
ifatt chnget "fatt"
ifdec chnget "fdec"
ifsus chnget "fsus"
ifrel chnget "frel"
kfenvamount chnget "fenvamount"
kcf chnget "cf"
kres chnget "res"

; Mix 
kpan chnget "pan"
kout chnget "out"
krm1 chnget "rm1"
krm2 chnget "rm2"

kcf portk kcf, 0.02
kres portk kres, 0.02

midinoteoncps p4, p5

;; TODO add scaling function
icps = p4
iamp = p5/127
ichn midichn

if ichn == 0 then
	ichn = p6
endif

;; TODO check of there are problems with these two!
aenv mxadsr iatt, idec, isus, irel
kfenv mxadsr ifatt, ifdec, ifsus, ifrel

;; TODO allow PWM?
aosc vco2 iamp, icps, 10
aosc moogladder aosc * aenv, kcf *(1+kfenv), kres

aoscL = aosc * (1 - kpan)
aoscR = aosc * kpan

gaRM1L = gaRM1L + (aoscL*krm1)
gaRM1R = gaRM1R + (aoscR*krm1)
gaRM2L = gaRM2L + (aoscL*krm2)
gaRM2R = gaRM2R + (aoscR*krm2)
gasigL = gasigL + (aoscL*kout)
gasigR = gasigR + (aoscR*kout)
endin

instr 80 ; Ring Modulator 1
krm1amount chnget "rm1amount"
krm1rate chnget "rm1rate"
krm1torm2 chnget "rm1torm2"

aosc poscil 1, krm1rate, gisine

armL = gaRM1L * aosc 
armR = gaRM1R * aosc

gasigL = gasigL + (armL * krm1amount)
gasigR = gasigR + (armR * krm1amount)

gaRM2L = gaRM2L + (armL * krm1torm2)
gaRM2R = gaRM2R + (armR * krm1torm2)

endin

instr 81 ; Ring Modulator 2
krm2amount chnget "rm2amount"
krm2rate chnget "rm2rate"

;; TODO add possibility to modulate with audio input?

aosc poscil krm2amount, krm2rate, gisine

armL = gaRM2L * aosc
armR = gaRM2R * aosc

gasigL = gasigL + armL
gasigR = gasigR + armR

endin

instr 99 ; Reverb
	koutlevel chnget "outlevel"
	krevmix chnget "revmix"
	kRoomSize chnget "Roomsize"
	kHFDamp chnget "HFDamp"
	;; TODO change freeverb if not sounding right
	; maybe make more of a "plate" reverb sound?, what would Asuar have used?
	aoutL, aoutR freeverb gasigL, gasigR, kRoomSize, kHFDamp, sr
	outs (aoutL * krevmix) + (gasigL * (1-krevmix)), (aoutR * krevmix) + (gasigR * (1-krevmix))
	clear gasigL, gasigR, gaRM1L, gaRM1R, gaRM2L, gaRM2R
endin


</CsInstruments>
<CsScore>
f 0 3600
</CsScore>
</CsoundSynthesizer>


<bsbPanel>
 <label>Widgets</label>
 <objectName/>
 <x>467</x>
 <y>272</y>
 <width>400</width>
 <height>200</height>
 <visible>true</visible>
 <uuid/>
 <bgcolor mode="nobackground">
  <r>231</r>
  <g>46</g>
  <b>255</b>
 </bgcolor>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>att</objectName>
  <x>35</x>
  <y>36</y>
  <width>20</width>
  <height>100</height>
  <uuid>{4103bd04-e7d3-470f-95d5-fd54ef691144}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.00100000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.07093000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>dec</objectName>
  <x>65</x>
  <y>36</y>
  <width>20</width>
  <height>100</height>
  <uuid>{801897bf-46f1-463f-bc87-1a143e439f23}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.09910000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>sus</objectName>
  <x>95</x>
  <y>36</y>
  <width>20</width>
  <height>100</height>
  <uuid>{c37fe6be-de56-412e-b3fd-d9ca6c6e7581}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.51490000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rel</objectName>
  <x>125</x>
  <y>36</y>
  <width>20</width>
  <height>100</height>
  <uuid>{59ed966d-60ae-428a-ba2a-1957bf0b2836}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.81190000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>fatt</objectName>
  <x>35</x>
  <y>177</y>
  <width>20</width>
  <height>100</height>
  <uuid>{efa861d4-9193-46d5-a45d-afa35d4d69bf}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.63370000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>fdec</objectName>
  <x>65</x>
  <y>177</y>
  <width>20</width>
  <height>100</height>
  <uuid>{f039c966-662b-4978-9fb4-9c21382a5498}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.57430000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>fsus</objectName>
  <x>95</x>
  <y>177</y>
  <width>20</width>
  <height>100</height>
  <uuid>{8b0505e3-02f3-4976-9268-602cb78db41a}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.41590000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>frel</objectName>
  <x>125</x>
  <y>177</y>
  <width>20</width>
  <height>100</height>
  <uuid>{7a2616a0-f1e0-4c41-8866-b7b94c41dfe3}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.01000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.96040000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>fenvamount</objectName>
  <x>174</x>
  <y>174</y>
  <width>20</width>
  <height>100</height>
  <uuid>{f8f190e1-1e8c-4438-9f37-8dca65fcbaee}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.00000000</minimum>
  <maximum>4.00000000</maximum>
  <value>2.36000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>cf</objectName>
  <x>204</x>
  <y>174</y>
  <width>20</width>
  <height>100</height>
  <uuid>{ae84eca4-7103-4763-b267-b4c95d016c27}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>100.00000000</minimum>
  <maximum>1000.00000000</maximum>
  <value>739.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>res</objectName>
  <x>234</x>
  <y>174</y>
  <width>20</width>
  <height>100</height>
  <uuid>{62e55728-91a9-4850-991f-a983e105b85c}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.50000000</minimum>
  <maximum>0.99000000</maximum>
  <value>0.90180000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBHSlider">
  <objectName>pan</objectName>
  <x>372</x>
  <y>150</y>
  <width>111</width>
  <height>34</height>
  <uuid>{29eec29f-914d-42fd-bbd6-bf265a37c28b}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.52252252</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>out</objectName>
  <x>319</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{07474eaa-ed2e-4748-9066-d51787bed870}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.43000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm1</objectName>
  <x>349</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{f38bd082-ba18-49d9-9483-f316b07b6818}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>1.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm2</objectName>
  <x>379</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{1d69b84b-be62-4271-8830-9952bb5ffa41}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>1.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm1amount</objectName>
  <x>409</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{d3eaa6e5-c625-4f72-8498-6671639c9d86}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm1rate</objectName>
  <x>439</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{1b225b79-bc31-4b22-9d7b-6e09a2d7f962}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.00000000</minimum>
  <maximum>50.00000000</maximum>
  <value>0.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm1torm2</objectName>
  <x>469</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{2ddff87a-c7f9-4803-8455-9dee70762548}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm2amount</objectName>
  <x>499</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{dfad3e65-7624-4cc3-b792-c3fc211ec0ce}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>1.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>rm2rate</objectName>
  <x>529</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{012e1f73-8b73-4fa2-902f-79b81c1358cb}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>0</midicc>
  <minimum>0.00000000</minimum>
  <maximum>50.00000000</maximum>
  <value>5.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>outlevel</objectName>
  <x>600</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{cc950949-9058-4290-bc0a-244f5ffd9723}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.25000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>revmix</objectName>
  <x>630</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{7c1650e4-7219-4335-9299-4af2353d7e18}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>0.53000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>Roomsize</objectName>
  <x>660</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{b23c6231-0eaf-4fae-8625-84ea5459c2e1}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>1.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
 <bsbObject version="2" type="BSBVSlider">
  <objectName>HFDamp</objectName>
  <x>690</x>
  <y>40</y>
  <width>20</width>
  <height>100</height>
  <uuid>{95d270e0-eec0-4113-ad7b-7da294ad147c}</uuid>
  <visible>true</visible>
  <midichan>0</midichan>
  <midicc>-3</midicc>
  <minimum>0.00000000</minimum>
  <maximum>1.00000000</maximum>
  <value>1.00000000</value>
  <mode>lin</mode>
  <mouseControl act="jump">continuous</mouseControl>
  <resolution>-1.00000000</resolution>
  <randomizable group="0">false</randomizable>
 </bsbObject>
</bsbPanel>
<bsbPresets>
</bsbPresets>
<EventPanel name="" tempo="120.00000000" loop="8.00000000" x="466" y="322" width="762" height="373" visible="true" loopStart="0" loopEnd="0">i 2 0 1 440 100 1 
i 2 1 1 220 100 1 
i 2 2 1 440 100 1 
i 2 3 1 220 100 1 
i 2 4 1 220 100 1 
i 2 5 1 330 100 1 
i 2 6 1 440 100 1 
i 2 7 1 660 100 1 
    
    
    </EventPanel>
