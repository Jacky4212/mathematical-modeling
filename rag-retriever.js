/**
 * RAG Retriever — 纯前端 TF-IDF 知识库检索引擎
 * 无需后端，加载 knowledge-chunks.json 后在浏览器端完成检索
 *
 * Usage:
 *   const rag = await RAGRetriever.init('/knowledge-chunks.json');
 *   const results = rag.retrieve('灰色预测适用于什么场景？', 3);
 *   // results = [{chunk, score, matchedKeywords}, ...]
 */
var RAGRetriever = (function(){
'use strict';

// ===== Tokenizer =====
// Chinese: character bigrams + unigrams
// English: word-level with stopword removal
var STOP_WORDS = new Set([
  '的','了','在','是','我','有','和','就','不','人','都','一','一个',
  '上','也','很','到','说','要','去','你','会','着','没有','看','好',
  '自己','这','他','她','它','们','那','些','什么','怎么','如何','可以',
  '因为','所以','但是','如果','虽然','而且','或者','并且','the','a','an',
  'is','are','was','were','be','been','being','have','has','had','do',
  'does','did','will','would','could','should','may','might','can','shall',
  'to','of','in','for','on','with','at','by','from','as','into','through',
  'during','before','after','above','below','between','and','or','not',
  'but','if','then','else','when','where','which','who','whom','whose',
  'this','that','these','those','it','its','they','them','their',
]);

function tokenize(text) {
  text = text.toLowerCase();

  // Extract English/technical words (keep as whole tokens)
  var terms = [];

  // Split: Chinese chars individually for bigrams, English words as-is
  var segments = text.split(/([a-zA-Z0-9_+\-().,/<>[\]{}]+)/);

  for (var si = 0; si < segments.length; si++) {
    var seg = segments[si].trim();
    if (!seg) continue;

    if (/^[a-zA-Z0-9_+\-().,/<>[\]{}]+$/.test(seg)) {
      // English/technical token
      var clean = seg.replace(/[(),/<>[\]{}]/g, ' ').trim();
      if (clean && clean.length >= 2) {
        var words = clean.split(/\s+/);
        for (var w = 0; w < words.length; w++) {
          var word = words[w];
          if (word.length >= 2 && !STOP_WORDS.has(word.toLowerCase())) {
            terms.push(word);
          }
        }
      }
    } else {
      // Chinese text — character bigrams
      var chars = seg.replace(/[\s\n\r\t\d.,;:!?，。；：！？、""''（）()【】\[\]《》<>\/\\|@#$%^&*+=\-~`]+/g, '').split('');
      for (var i = 0; i < chars.length; i++) {
        var ch = chars[i];
        if (!STOP_WORDS.has(ch) && ch.trim()) {
          terms.push(ch); // unigram
        }
        if (i < chars.length - 1) {
          var bigram = chars[i] + chars[i+1];
          if (!STOP_WORDS.has(chars[i]) && !STOP_WORDS.has(chars[i+1])) {
            terms.push(bigram); // bigram
          }
        }
      }
    }
  }

  return terms;
}

// ===== TF-IDF Engine =====
function buildIndex(chunks) {
  var docTerms = [];       // tokenized docs
  var docFreq = {};        // document frequency for each term
  var N = chunks.length;

  // Tokenize all documents
  for (var i = 0; i < N; i++) {
    var tokens = tokenize(chunks[i].search_text);
    // Count term frequency within doc
    var tf = {};
    for (var j = 0; j < tokens.length; j++) {
      var t = tokens[j];
      tf[t] = (tf[t] || 0) + 1;
    }
    docTerms.push(tf);

    // Build document frequency
    var seen = {};
    for (var j = 0; j < tokens.length; j++) {
      var t = tokens[j];
      if (!seen[t]) {
        docFreq[t] = (docFreq[t] || 0) + 1;
        seen[t] = true;
      }
    }
  }

  // Compute IDF for each term
  var idf = {};
  for (var t in docFreq) {
    idf[t] = Math.log((N - docFreq[t] + 0.5) / (docFreq[t] + 0.5) + 1);
  }

  // Normalize doc vectors to unit length (for cosine similarity)
  var docVectors = [];
  for (var i = 0; i < N; i++) {
    var tf = docTerms[i];
    var norm = 0;
    var vec = {};
    for (var t in tf) {
      var w = tf[t] * (idf[t] || 0);
      vec[t] = w;
      norm += w * w;
    }
    norm = Math.sqrt(norm) || 1;
    for (var t in vec) {
      vec[t] /= norm;
    }
    docVectors.push(vec);
  }

  return { docVectors: docVectors, idf: idf, N: N };
}

// ===== Retriever Class =====
function Retriever(chunks) {
  this.chunks = chunks;
  this.index = buildIndex(chunks);
}

Retriever.prototype.retrieve = function(query, topK) {
  topK = topK || 3;
  var queryTokens = tokenize(query);

  // Compute query TF vector
  var qt = {};
  for (var i = 0; i < queryTokens.length; i++) {
    var t = queryTokens[i];
    qt[t] = (qt[t] || 0) + 1;
  }

  // Normalize query vector with IDF
  var qnorm = 0;
  var qvec = {};
  for (var t in qt) {
    var w = qt[t] * (this.index.idf[t] || 0);
    qvec[t] = w;
    qnorm += w * w;
  }
  qnorm = Math.sqrt(qnorm) || 1;
  for (var t in qvec) {
    qvec[t] /= qnorm;
  }

  // If query has no meaningful terms, return empty
  if (qnorm <= 1e-10) return [];

  // Cosine similarity with all docs
  var scores = [];
  for (var i = 0; i < this.index.N; i++) {
    var dvec = this.index.docVectors[i];
    var dot = 0;
    for (var t in qvec) {
      if (dvec[t]) dot += qvec[t] * dvec[t];
    }
    if (dot > 0) {
      // Bonus for keyword matches in title
      var kwBonus = 0;
      var chunk = this.chunks[i];
      for (var j = 0; j < (chunk.keywords || []).length; j++) {
        if (query.toLowerCase().indexOf(chunk.keywords[j].toLowerCase()) >= 0) {
          kwBonus += 0.1;
        }
      }
      scores.push({ idx: i, score: dot + kwBonus });
    }
  }

  // Sort by score descending
  scores.sort(function(a, b) { return b.score - a.score; });

  // Return top K results
  var results = [];
  for (var i = 0; i < Math.min(topK, scores.length); i++) {
    var s = scores[i];
    var chunk = this.chunks[s.idx];
    // Find which keywords were matched
    var matchedKw = [];
    var ql = query.toLowerCase();
    for (var j = 0; j < (chunk.keywords || []).length; j++) {
      if (ql.indexOf(chunk.keywords[j].toLowerCase()) >= 0) {
        matchedKw.push(chunk.keywords[j]);
      }
    }
    results.push({
      chunk: chunk,
      score: s.score,
      matchedKeywords: matchedKw,
    });
  }

  return results;
};

// ===== Public API =====
var _retriever = null;

return {
  /**
   * Initialize the retriever by loading knowledge chunks.
   * @param {string} url - URL to knowledge-chunks.json
   * @returns {Promise} resolves when ready
   */
  init: function(url) {
    if (_retriever) return Promise.resolve(_retriever);

    return fetch(url)
      .then(function(r) {
        if (!r.ok) throw new Error('Failed to load knowledge base: ' + r.status);
        return r.json();
      })
      .then(function(chunks) {
        if (!Array.isArray(chunks) || chunks.length === 0) {
          throw new Error('Knowledge base is empty or invalid');
        }
        _retriever = new Retriever(chunks);
        console.log('[RAG] Knowledge base loaded: ' + chunks.length + ' chunks');
        return _retriever;
      });
  },

  /**
   * Retrieve relevant knowledge chunks for a query.
   * @param {string} query - User's question
   * @param {number} topK - Number of results (default 3)
   * @returns {Array} [{chunk, score, matchedKeywords}, ...]
   */
  retrieve: function(query, topK) {
    if (!_retriever) {
      console.warn('[RAG] Retriever not initialized, call init() first');
      return [];
    }
    return _retriever.retrieve(query, topK || 3);
  },

  /**
   * Build a context string from retrieved chunks for prompt injection.
   * @param {Array} results - Results from retrieve()
   * @param {number} maxTokens - Max context tokens (default ~2000)
   * @returns {string} Formatted context string
   */
  buildContext: function(results, maxTokens) {
    maxTokens = maxTokens || 2000;
    if (!results || results.length === 0) return '';

    var context = '【内部知识库匹配结果】\n';
    var charBudget = maxTokens * 4; // rough: 1 token ≈ 4 chars
    var used = context.length;

    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var ctx = r.chunk.context;
      // Score badge
      var scorePct = Math.round(r.score * 100);
      var header = '\n--- 匹配' + (i+1) + ' (相关度:' + scorePct + '%) [' + r.chunk.category + '] ---\n';
      var body = ctx.length > (charBudget - used - header.length)
        ? ctx.substring(0, charBudget - used - header.length - 20) + '...[截断]'
        : ctx;

      if (used + header.length + body.length > charBudget) {
        body = ctx.substring(0, Math.max(0, charBudget - used - header.length - 20)) + '...[截断]';
      }

      context += header + body;
      used += header.length + body.length;
      if (used >= charBudget) break;
    }

    return context;
  },

  /** Check if retriever is ready */
  isReady: function() { return !!_retriever; },

  /** Get total chunk count */
  getChunkCount: function() { return _retriever ? _retriever.chunks.length : 0; },

  /** Get category list */
  getCategories: function() {
    if (!_retriever) return [];
    var cats = {};
    for (var i = 0; i < _retriever.chunks.length; i++) {
      cats[_retriever.chunks[i].category] = (cats[_retriever.chunks[i].category] || 0) + 1;
    }
    return cats;
  },
};

})();
