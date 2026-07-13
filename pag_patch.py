# Generalized paginator gap-fill for Blood & Grit companion books.
# Replaces splitBox with a general splitContainer that splits ANY container
# (prose box, two-column block, or stat block) across a page boundary, so
# whitespace is filled instead of blocks moving whole. Applied at build time
# to a fresh clone of the Player's Book shell (Player's Book itself untouched).

_ORIG_SPLITBOX = '''    function splitBox(box){
      var list=box.querySelector(':scope > ul, :scope > ol');
      if(!list){ firstPlaced=true; return; }
      var notAlone=!!box.previousElementSibling;
      var items=[].slice.call(list.children);
      for(var k=0;k<items.length;k++){ list.removeChild(items[k]); }
      var curList=list, i=0;
      while(i<items.length){
        curList.appendChild(items[i]);
        if(!fits(cur.content,max)){
          if(curList.children.length>1){
            curList.removeChild(items[i]);
            fresh();
            var nb=box.cloneNode(false);
            var nl=list.cloneNode(false);
            nb.appendChild(nl);
            cur.content.appendChild(nb);
            curList=nl; notAlone=false;
          } else if(notAlone){
            /* heading + first item won't fit this gap: move the whole box to a
               fresh page rather than clip it (mirrors splitTable). */
            curList.removeChild(items[i]);
            if(box.parentNode) box.parentNode.removeChild(box);
            fresh();
            cur.content.appendChild(box);
            curList=list; notAlone=false;
          } else { i++; }
        } else { i++; }
      }
      firstPlaced=true;
    }'''

_NEW_SPLIT = '''    function _mkFrag(box, head){
      fresh();
      var nb=box.cloneNode(false);
      if(head){ var nh=head.cloneNode(true); nh.innerHTML+=' <span class="sb-cont">(cont.)</span>'; nb.appendChild(nh); }
      cur.content.appendChild(nb);
      return nb;
    }
    function splitContainer(box, headSel){
      var head=headSel?box.querySelector(':scope > '+headSel):null;
      var items=[].slice.call(box.children).filter(function(c){return c!==head;});
      for(var k=0;k<items.length;k++){ box.removeChild(items[k]); }
      var notAlone=!!box.previousElementSibling;
      var curBox=box, placed=0, i=0;
      while(i<items.length){
        var item=items[i];
        curBox.appendChild(item);
        if(fits(cur.content,max)){ i++; placed++; continue; }
        /* a multi-item list child can itself be split across fragments */
        if((item.tagName==='UL'||item.tagName==='OL') && item.children.length>1){
          var lis=[].slice.call(item.children);
          for(var z=0;z<lis.length;z++){ item.removeChild(lis[z]); }
          var curList=item, lp=0, li=0;
          while(li<lis.length){
            curList.appendChild(lis[li]);
            if(fits(cur.content,max)){ li++; lp++; placed++; continue; }
            if(lp>0){
              curList.removeChild(lis[li]);
              curBox=_mkFrag(box, head);
              var nl=item.cloneNode(false); curBox.appendChild(nl); curList=nl; lp=0;
            } else if(placed>0 || notAlone){
              curList.removeChild(lis[li]);
              if(curList.parentNode && !curList.children.length){ curList.parentNode.removeChild(curList); }
              curBox=_mkFrag(box, head);
              var nl2=item.cloneNode(false); curBox.appendChild(nl2); curList=nl2; lp=0; notAlone=false;
            } else { li++; lp++; placed++; }
          }
          i++; placed++; continue;
        }
        if(placed>0){
          curBox.removeChild(item);
          curBox=_mkFrag(box, head); placed=0; notAlone=false;
          /* retry the same item on the fresh fragment (do not advance i) */
        } else if(notAlone){
          /* header + first item won't fit this gap: move the whole box whole */
          curBox.removeChild(item);
          if(curBox.parentNode) curBox.parentNode.removeChild(curBox);
          fresh();
          var ob=box.cloneNode(false); if(head) ob.appendChild(head.cloneNode(true));
          for(var j=i;j<items.length;j++){ ob.appendChild(items[j]); }
          cur.content.appendChild(ob); firstPlaced=true; return;
        } else { i++; placed++; }
      }
      firstPlaced=true;
    }
    function splitBox(box){ splitContainer(box, 'h4'); }
    function splitStatblock(box){ splitContainer(box, '.sb-head'); }'''

_ORIG_TOOBIG = '''    function tooBig(block){
      if(block.tagName==='TABLE'){ splitTable(block); }
      else if(block.tagName==='UL'||block.tagName==='OL'){ splitList(block); }
      else if(block.tagName==='DIV'){ splitBox(block); }
      else { firstPlaced=true; }
    }'''
_NEW_TOOBIG = '''    function tooBig(block){
      if(block.tagName==='TABLE'){ splitTable(block); }
      else if(block.tagName==='UL'||block.tagName==='OL'){ splitList(block); }
      else if(block.tagName==='DIV'){
        if(block.classList && block.classList.contains('statblock')) splitContainer(block, '.sb-head');
        else if(block.classList && block.classList.contains('twocol')) splitContainer(block, null);
        else if(block.classList && block.classList.contains('creature')) splitContainer(block, '.cr-name');
        else splitBox(block);
      }
      else { firstPlaced=true; }
    }'''

_ORIG_SF = '''      if(b.tagName==='DIV' && b.classList && b.classList.contains('box')){
        var lst=b.querySelector(':scope > ul, :scope > ol');
        return !!lst && lst.children.length>1 && lst===b.lastElementChild;
      }
      return false;
    }'''
_NEW_SF = '''      if(b.tagName==='DIV' && b.classList){
        if(b.classList.contains('statblock')) return b.querySelectorAll(':scope > p').length>1;
        if(b.classList.contains('twocol')) return b.children.length>1;
        if(b.classList.contains('creature')) return b.children.length>1;
        if(b.classList.contains('box')){
          var h=b.querySelector(':scope > h4');
          var kids=[].slice.call(b.children).filter(function(c){return c!==h;});
          if(kids.length>1) return true;
          var lst=b.querySelector(':scope > ul, :scope > ol');
          return !!lst && lst.children.length>1;
        }
      }
      return false;
    }'''

_CSS = '  /*sbcont*/ .sb-cont{ font-style:italic; font-weight:400; color:var(--ink-soft); font-size:12px; letter-spacing:0; }\n</style>'


def patch_paginator(s):
    # Since the v2.11/v2.3 feathering paginator (2026-07-11), the shared shell
    # script carries splitContainer / creature / statblock splitting natively,
    # and the .sb-cont CSS lives in player-src.html — this patch is a no-op.
    # The guards keep the old behavior available if an old shell ever comes back.
    if 'FEATHER_MAX' in s and 'splitContainer' in s:
        assert '.sb-cont' in s, "feathering shell is missing the .sb-cont CSS"
        return s
    assert _ORIG_SPLITBOX in s, "splitBox anchor missing"
    s = s.replace(_ORIG_SPLITBOX, _NEW_SPLIT, 1)
    assert _ORIG_TOOBIG in s, "tooBig anchor missing"
    s = s.replace(_ORIG_TOOBIG, _NEW_TOOBIG, 1)
    assert _ORIG_SF in s, "isSplitFill anchor missing"
    s = s.replace(_ORIG_SF, _NEW_SF, 1)
    if '/*sbcont*/' not in s:
        s = s.replace('</style>', _CSS, 1)
    return s
