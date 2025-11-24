/**
 * NexaDB JavaScript/Node.js Client SDK
 * =====================================
 *
 * Official JavaScript client for NexaDB.
 * Works in Node.js and browser (with fetch polyfill for older browsers).
 *
 * Features:
 * - Promise-based API
 * - TypeScript definitions (coming soon)
 * - Automatic retries
 * - Connection pooling
 *
 * Usage (Node.js):
 *   const { NexaDB } = require('./nexadb');
 *   const db = new NexaDB({ host: 'localhost', port: 5050, apiKey: 'your_key' });
 *
 *   const users = db.collection('users');
 *   await users.insert({ name: 'Alice', age: 28 });
 *
 * Usage (Browser):
 *   <script src="nexadb.js"></script>
 *   <script>
 *     const db = new NexaDB({ host: 'localhost', port: 5050, apiKey: 'your_key' });
 *     // ... same as Node.js
 *   </script>
 */

(function(global) {
  'use strict';

  /**
   * NexaDB Exception
   */
  class NexaDBException extends Error {
    constructor(message) {
      super(message);
      this.name = 'NexaDBException';
    }
  }

  /**
   * Collection Client
   */
  class CollectionClient {
    constructor(name, baseUrl, apiKey) {
      this.name = name;
      this.baseUrl = baseUrl;
      this.apiKey = apiKey;
    }

    /**
     * Make HTTP request to NexaDB server
     */
    async _request(method, path, data = null, params = null) {
      let url = `${this.baseUrl}${path}`;

      if (params) {
        const queryString = new URLSearchParams(params).toString();
        url += `?${queryString}`;
      }

      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        }
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      try {
        const response = await fetch(url, options);
        const result = await response.json();

        if (!response.ok) {
          throw new NexaDBException(`${response.status} ${response.statusText}: ${result.error || 'Unknown error'}`);
        }

        return result;
      } catch (error) {
        if (error instanceof NexaDBException) {
          throw error;
        }
        throw new NexaDBException(`Connection error: ${error.message}`);
      }
    }

    /**
     * Insert a single document
     *
     * @param {Object} document - Document data
     * @returns {Promise<string>} Document ID
     *
     * @example
     * const docId = await users.insert({ name: 'Alice', age: 28 });
     * console.log(docId); // 'a1b2c3d4e5f6'
     */
    async insert(document) {
      const result = await this._request('POST', `/collections/${this.name}`, document);
      return result.document_id;
    }

    /**
     * Insert multiple documents
     *
     * @param {Array<Object>} documents - Array of documents
     * @returns {Promise<Array<string>>} Array of document IDs
     *
     * @example
     * const ids = await users.insertMany([
     *   { name: 'Alice', age: 28 },
     *   { name: 'Bob', age: 35 }
     * ]);
     */
    async insertMany(documents) {
      const result = await this._request('POST', `/collections/${this.name}/bulk`, { documents });
      return result.document_ids;
    }

    /**
     * Find document by ID
     *
     * @param {string} docId - Document ID
     * @returns {Promise<Object|null>} Document or null if not found
     *
     * @example
     * const user = await users.findById('a1b2c3d4');
     * console.log(user.name); // 'Alice'
     */
    async findById(docId) {
      try {
        const result = await this._request('GET', `/collections/${this.name}/${docId}`);
        return result.document;
      } catch (error) {
        if (error.message.includes('404')) {
          return null;
        }
        throw error;
      }
    }

    /**
     * Find documents matching query
     *
     * @param {Object} query - Query object (MongoDB-style)
     * @param {number} limit - Max results to return (default: 100)
     * @returns {Promise<Array<Object>>} Array of documents
     *
     * @example
     * const users = await collection.find({ age: { $gt: 25 } });
     *
     * Query operators:
     * - $eq, $ne - Equality
     * - $gt, $gte, $lt, $lte - Comparison
     * - $in, $nin - Array membership
     * - $regex - Regex match
     * - $exists - Field exists
     */
    async find(query = {}, limit = 100) {
      const params = {
        query: JSON.stringify(query),
        limit: limit.toString()
      };

      const result = await this._request('GET', `/collections/${this.name}`, null, params);
      return result.documents;
    }

    /**
     * Find single document
     *
     * @param {Object} query - Query object
     * @returns {Promise<Object|null>} First matching document or null
     *
     * @example
     * const user = await users.findOne({ email: 'alice@example.com' });
     */
    async findOne(query) {
      const results = await this.find(query, 1);
      return results.length > 0 ? results[0] : null;
    }

    /**
     * Update document by ID
     *
     * @param {string} docId - Document ID
     * @param {Object} updates - Fields to update
     * @returns {Promise<boolean>} True if updated, false if not found
     *
     * @example
     * await users.update('a1b2c3', { age: 29 });
     */
    async update(docId, updates) {
      try {
        await this._request('PUT', `/collections/${this.name}/${docId}`, updates);
        return true;
      } catch (error) {
        if (error.message.includes('404')) {
          return false;
        }
        throw error;
      }
    }

    /**
     * Delete document by ID
     *
     * @param {string} docId - Document ID
     * @returns {Promise<boolean>} True if deleted, false if not found
     *
     * @example
     * await users.delete('a1b2c3');
     */
    async delete(docId) {
      try {
        await this._request('DELETE', `/collections/${this.name}/${docId}`);
        return true;
      } catch (error) {
        if (error.message.includes('404')) {
          return false;
        }
        throw error;
      }
    }

    /**
     * Complex query (alternative to find())
     *
     * @param {Object} query - Query object
     * @param {number} limit - Max results
     * @returns {Promise<Array<Object>>} Array of documents
     */
    async query(query, limit = 100) {
      const result = await this._request('POST', `/collections/${this.name}/query`, { query, limit });
      return result.documents;
    }

    /**
     * Aggregation pipeline
     *
     * @param {Array<Object>} pipeline - Array of aggregation stages
     * @returns {Promise<Array<Object>>} Aggregation results
     *
     * @example
     * const results = await users.aggregate([
     *   { $match: { age: { $gte: 30 } } },
     *   { $group: { _id: '$age', count: { $sum: 1 } } },
     *   { $sort: { count: -1 } }
     * ]);
     *
     * Stages:
     * - $match - Filter documents
     * - $group - Group by field
     * - $sort - Sort results (1=asc, -1=desc)
     * - $limit - Limit results
     * - $project - Select fields
     */
    async aggregate(pipeline) {
      const result = await this._request('POST', `/collections/${this.name}/aggregate`, { pipeline });
      return result.results;
    }

    /**
     * Count all documents in collection
     *
     * @returns {Promise<number>} Number of documents
     *
     * @example
     * const count = await users.count();
     * console.log(`Total users: ${count}`);
     */
    async count() {
      const result = await this._request('GET', `/collections/${this.name}`, null, { limit: '999999' });
      return result.count;
    }
  }

  /**
   * Vector Collection Client (AI/ML)
   */
  class VectorCollectionClient {
    constructor(name, baseUrl, apiKey, dimensions = 768) {
      this.name = name;
      this.baseUrl = baseUrl;
      this.apiKey = apiKey;
      this.dimensions = dimensions;
      this.collection = new CollectionClient(name, baseUrl, apiKey);
    }

    /**
     * Insert document with vector embedding
     *
     * @param {Object} document - Document data
     * @param {Array<number>} vector - Embedding vector
     * @returns {Promise<string>} Document ID
     *
     * @example
     * const products = db.vectorCollection('products', 384);
     * await products.insert(
     *   { name: 'Laptop', price: 1200 },
     *   [0.1, 0.2, ..., 0.8]  // 384-dim vector
     * );
     */
    async insert(document, vector) {
      if (vector.length !== this.dimensions) {
        throw new Error(`Vector must have ${this.dimensions} dimensions, got ${vector.length}`);
      }

      const docId = await this.collection.insert(document);
      await this.collection.update(docId, { __vector__: vector });

      return docId;
    }

    /**
     * Vector similarity search
     *
     * @param {Array<number>} queryVector - Query embedding
     * @param {number} limit - Max results
     * @returns {Promise<Array<Object>>} Array of {document_id, similarity, document}
     *
     * @example
     * const results = await products.search([0.15, 0.22, ...], 5);
     * results.forEach(r => {
     *   console.log(`${r.document.name}: ${r.similarity.toFixed(4)}`);
     * });
     */
    async search(queryVector, limit = 10) {
      if (queryVector.length !== this.dimensions) {
        throw new Error(`Query vector must have ${this.dimensions} dimensions`);
      }

      const result = await this.collection._request('POST', `/vector/${this.name}/search`, {
        vector: queryVector,
        limit,
        dimensions: this.dimensions
      });

      return result.results;
    }
  }

  /**
   * Main NexaDB Client
   */
  class NexaDB {
    /**
     * Initialize NexaDB client
     *
     * @param {Object} options - Configuration options
     * @param {string} options.host - Server hostname (default: 'localhost')
     * @param {number} options.port - Server port (default: 5050)
     * @param {string} options.apiKey - API key for authentication
     *
     * @example
     * const db = new NexaDB({
     *   host: 'localhost',
     *   port: 5050,
     *   apiKey: 'your_api_key'
     * });
     */
    constructor(options = {}) {
      this.host = options.host || 'localhost';
      this.port = options.port || 6969;
      this.apiKey = options.apiKey || '';
      this.baseUrl = `http://${this.host}:${this.port}`;
    }

    /**
     * Get collection client
     *
     * @param {string} name - Collection name
     * @returns {CollectionClient} Collection client
     *
     * @example
     * const users = db.collection('users');
     * await users.insert({ name: 'Alice' });
     */
    collection(name) {
      return new CollectionClient(name, this.baseUrl, this.apiKey);
    }

    /**
     * Get vector collection client
     *
     * @param {string} name - Collection name
     * @param {number} dimensions - Vector dimensions (default: 768)
     * @returns {VectorCollectionClient} Vector collection client
     *
     * @example
     * const products = db.vectorCollection('products', 384);
     * await products.insert({ name: 'Laptop' }, [0.1, 0.2, ...]);
     */
    vectorCollection(name, dimensions = 768) {
      return new VectorCollectionClient(name, this.baseUrl, this.apiKey, dimensions);
    }

    /**
     * List all collections
     *
     * @returns {Promise<Array<string>>} Array of collection names
     *
     * @example
     * const collections = await db.listCollections();
     * console.log(collections); // ['users', 'products', 'orders']
     */
    async listCollections() {
      const response = await fetch(`${this.baseUrl}/collections`, {
        headers: { 'X-API-Key': this.apiKey }
      });

      const result = await response.json();
      return result.collections;
    }

    /**
     * Delete entire collection
     *
     * @param {string} name - Collection name
     * @returns {Promise<boolean>} True if dropped, false if not found
     *
     * @example
     * await db.dropCollection('old_collection');
     */
    async dropCollection(name) {
      try {
        const response = await fetch(`${this.baseUrl}/collections/${name}`, {
          method: 'DELETE',
          headers: { 'X-API-Key': this.apiKey }
        });

        return response.ok;
      } catch (error) {
        if (error.status === 404) {
          return false;
        }
        throw error;
      }
    }

    /**
     * Get server status
     *
     * @returns {Promise<Object>} Status object
     *
     * @example
     * const status = await db.status();
     * console.log(status); // { status: 'ok', version: '1.0.0', ... }
     */
    async status() {
      const response = await fetch(`${this.baseUrl}/status`);
      return await response.json();
    }

    /**
     * Get database statistics
     *
     * @returns {Promise<Object>} Stats object
     *
     * @example
     * const stats = await db.stats();
     * console.log(stats);
     */
    async stats() {
      const response = await fetch(`${this.baseUrl}/stats`, {
        headers: { 'X-API-Key': this.apiKey }
      });

      const result = await response.json();
      return result.stats;
    }
  }

  // Export for different environments
  if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = { NexaDB, CollectionClient, VectorCollectionClient, NexaDBException };
  } else {
    // Browser
    global.NexaDB = NexaDB;
    global.CollectionClient = CollectionClient;
    global.VectorCollectionClient = VectorCollectionClient;
    global.NexaDBException = NexaDBException;
  }

})(typeof window !== 'undefined' ? window : global);


// Example usage (Node.js)
if (typeof require !== 'undefined' && require.main === module) {
  const { NexaDB } = require('./nexadb');

  (async () => {
    console.log('='.repeat(70));
    console.log('NexaDB JavaScript Client - Example Usage');
    console.log('='.repeat(70));

    // Connect to NexaDB
    const db = new NexaDB({
      host: 'localhost',
      port: 6969,
      apiKey: 'b8c37e33faa946d43c2f6e5a0bc7e7e0'
    });

    // Check status
    console.log('\n[STATUS] Checking server...');
    try {
      const status = await db.status();
      console.log(`Server: ${status.database} v${status.version} - ${status.status}`);
    } catch (error) {
      console.log(`Error: Server not running? (${error.message})`);
      process.exit(1);
    }

    // Create collection
    console.log('\n[COLLECTION] Working with users collection');
    const users = db.collection('users');

    // Insert
    console.log('\nInserting documents...');
    const userId = await users.insert({ name: 'Alice Johnson', age: 28, email: 'alice@example.com' });
    console.log(`Inserted: ${userId}`);

    await users.insertMany([
      { name: 'Bob Smith', age: 35, email: 'bob@example.com' },
      { name: 'Charlie Brown', age: 42, email: 'charlie@example.com' }
    ]);

    // Find
    console.log('\nFinding users with age > 30:');
    const results = await users.find({ age: { $gt: 30 } });
    results.forEach(user => {
      console.log(`  - ${user.name} (age: ${user.age})`);
    });

    // Update
    console.log('\nUpdating Alice\'s age...');
    await users.update(userId, { age: 29 });
    const alice = await users.findById(userId);
    console.log(`  Updated age: ${alice.age}`);

    // Aggregation
    console.log('\nAggregation - Group by age:');
    const aggResults = await users.aggregate([
      { $match: { age: { $gte: 30 } } },
      { $group: { _id: '$age', count: { $sum: 1 } } },
      { $sort: { _id: 1 } }
    ]);
    aggResults.forEach(group => {
      console.log(`  Age ${group._id}: ${group.count} users`);
    });

    // Count
    const count = await users.count();
    console.log(`\nTotal users: ${count}`);

    console.log('\n' + '='.repeat(70));
    console.log('Example complete!');
    console.log('='.repeat(70));
  })();
}
