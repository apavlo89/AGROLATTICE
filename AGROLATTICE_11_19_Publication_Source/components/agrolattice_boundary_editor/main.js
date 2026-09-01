(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // ../../../../../tmp/agrolattice_component_build/node_modules/react-is/cjs/react-is.development.js
  var require_react_is_development = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/react-is/cjs/react-is.development.js"(exports) {
      "use strict";
      if (true) {
        (function() {
          "use strict";
          var hasSymbol = typeof Symbol === "function" && Symbol.for;
          var REACT_ELEMENT_TYPE = hasSymbol ? Symbol.for("react.element") : 60103;
          var REACT_PORTAL_TYPE = hasSymbol ? Symbol.for("react.portal") : 60106;
          var REACT_FRAGMENT_TYPE = hasSymbol ? Symbol.for("react.fragment") : 60107;
          var REACT_STRICT_MODE_TYPE = hasSymbol ? Symbol.for("react.strict_mode") : 60108;
          var REACT_PROFILER_TYPE = hasSymbol ? Symbol.for("react.profiler") : 60114;
          var REACT_PROVIDER_TYPE = hasSymbol ? Symbol.for("react.provider") : 60109;
          var REACT_CONTEXT_TYPE = hasSymbol ? Symbol.for("react.context") : 60110;
          var REACT_ASYNC_MODE_TYPE = hasSymbol ? Symbol.for("react.async_mode") : 60111;
          var REACT_CONCURRENT_MODE_TYPE = hasSymbol ? Symbol.for("react.concurrent_mode") : 60111;
          var REACT_FORWARD_REF_TYPE = hasSymbol ? Symbol.for("react.forward_ref") : 60112;
          var REACT_SUSPENSE_TYPE = hasSymbol ? Symbol.for("react.suspense") : 60113;
          var REACT_SUSPENSE_LIST_TYPE = hasSymbol ? Symbol.for("react.suspense_list") : 60120;
          var REACT_MEMO_TYPE = hasSymbol ? Symbol.for("react.memo") : 60115;
          var REACT_LAZY_TYPE = hasSymbol ? Symbol.for("react.lazy") : 60116;
          var REACT_BLOCK_TYPE = hasSymbol ? Symbol.for("react.block") : 60121;
          var REACT_FUNDAMENTAL_TYPE = hasSymbol ? Symbol.for("react.fundamental") : 60117;
          var REACT_RESPONDER_TYPE = hasSymbol ? Symbol.for("react.responder") : 60118;
          var REACT_SCOPE_TYPE = hasSymbol ? Symbol.for("react.scope") : 60119;
          function isValidElementType(type2) {
            return typeof type2 === "string" || typeof type2 === "function" || // Note: its typeof might be other than 'symbol' or 'number' if it's a polyfill.
            type2 === REACT_FRAGMENT_TYPE || type2 === REACT_CONCURRENT_MODE_TYPE || type2 === REACT_PROFILER_TYPE || type2 === REACT_STRICT_MODE_TYPE || type2 === REACT_SUSPENSE_TYPE || type2 === REACT_SUSPENSE_LIST_TYPE || typeof type2 === "object" && type2 !== null && (type2.$$typeof === REACT_LAZY_TYPE || type2.$$typeof === REACT_MEMO_TYPE || type2.$$typeof === REACT_PROVIDER_TYPE || type2.$$typeof === REACT_CONTEXT_TYPE || type2.$$typeof === REACT_FORWARD_REF_TYPE || type2.$$typeof === REACT_FUNDAMENTAL_TYPE || type2.$$typeof === REACT_RESPONDER_TYPE || type2.$$typeof === REACT_SCOPE_TYPE || type2.$$typeof === REACT_BLOCK_TYPE);
          }
          function typeOf(object) {
            if (typeof object === "object" && object !== null) {
              var $$typeof = object.$$typeof;
              switch ($$typeof) {
                case REACT_ELEMENT_TYPE:
                  var type2 = object.type;
                  switch (type2) {
                    case REACT_ASYNC_MODE_TYPE:
                    case REACT_CONCURRENT_MODE_TYPE:
                    case REACT_FRAGMENT_TYPE:
                    case REACT_PROFILER_TYPE:
                    case REACT_STRICT_MODE_TYPE:
                    case REACT_SUSPENSE_TYPE:
                      return type2;
                    default:
                      var $$typeofType = type2 && type2.$$typeof;
                      switch ($$typeofType) {
                        case REACT_CONTEXT_TYPE:
                        case REACT_FORWARD_REF_TYPE:
                        case REACT_LAZY_TYPE:
                        case REACT_MEMO_TYPE:
                        case REACT_PROVIDER_TYPE:
                          return $$typeofType;
                        default:
                          return $$typeof;
                      }
                  }
                case REACT_PORTAL_TYPE:
                  return $$typeof;
              }
            }
            return void 0;
          }
          var AsyncMode = REACT_ASYNC_MODE_TYPE;
          var ConcurrentMode = REACT_CONCURRENT_MODE_TYPE;
          var ContextConsumer = REACT_CONTEXT_TYPE;
          var ContextProvider = REACT_PROVIDER_TYPE;
          var Element2 = REACT_ELEMENT_TYPE;
          var ForwardRef = REACT_FORWARD_REF_TYPE;
          var Fragment = REACT_FRAGMENT_TYPE;
          var Lazy = REACT_LAZY_TYPE;
          var Memo = REACT_MEMO_TYPE;
          var Portal = REACT_PORTAL_TYPE;
          var Profiler = REACT_PROFILER_TYPE;
          var StrictMode = REACT_STRICT_MODE_TYPE;
          var Suspense = REACT_SUSPENSE_TYPE;
          var hasWarnedAboutDeprecatedIsAsyncMode = false;
          function isAsyncMode(object) {
            {
              if (!hasWarnedAboutDeprecatedIsAsyncMode) {
                hasWarnedAboutDeprecatedIsAsyncMode = true;
                console["warn"]("The ReactIs.isAsyncMode() alias has been deprecated, and will be removed in React 17+. Update your code to use ReactIs.isConcurrentMode() instead. It has the exact same API.");
              }
            }
            return isConcurrentMode(object) || typeOf(object) === REACT_ASYNC_MODE_TYPE;
          }
          function isConcurrentMode(object) {
            return typeOf(object) === REACT_CONCURRENT_MODE_TYPE;
          }
          function isContextConsumer(object) {
            return typeOf(object) === REACT_CONTEXT_TYPE;
          }
          function isContextProvider(object) {
            return typeOf(object) === REACT_PROVIDER_TYPE;
          }
          function isElement(object) {
            return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
          }
          function isForwardRef(object) {
            return typeOf(object) === REACT_FORWARD_REF_TYPE;
          }
          function isFragment(object) {
            return typeOf(object) === REACT_FRAGMENT_TYPE;
          }
          function isLazy(object) {
            return typeOf(object) === REACT_LAZY_TYPE;
          }
          function isMemo(object) {
            return typeOf(object) === REACT_MEMO_TYPE;
          }
          function isPortal(object) {
            return typeOf(object) === REACT_PORTAL_TYPE;
          }
          function isProfiler(object) {
            return typeOf(object) === REACT_PROFILER_TYPE;
          }
          function isStrictMode(object) {
            return typeOf(object) === REACT_STRICT_MODE_TYPE;
          }
          function isSuspense(object) {
            return typeOf(object) === REACT_SUSPENSE_TYPE;
          }
          exports.AsyncMode = AsyncMode;
          exports.ConcurrentMode = ConcurrentMode;
          exports.ContextConsumer = ContextConsumer;
          exports.ContextProvider = ContextProvider;
          exports.Element = Element2;
          exports.ForwardRef = ForwardRef;
          exports.Fragment = Fragment;
          exports.Lazy = Lazy;
          exports.Memo = Memo;
          exports.Portal = Portal;
          exports.Profiler = Profiler;
          exports.StrictMode = StrictMode;
          exports.Suspense = Suspense;
          exports.isAsyncMode = isAsyncMode;
          exports.isConcurrentMode = isConcurrentMode;
          exports.isContextConsumer = isContextConsumer;
          exports.isContextProvider = isContextProvider;
          exports.isElement = isElement;
          exports.isForwardRef = isForwardRef;
          exports.isFragment = isFragment;
          exports.isLazy = isLazy;
          exports.isMemo = isMemo;
          exports.isPortal = isPortal;
          exports.isProfiler = isProfiler;
          exports.isStrictMode = isStrictMode;
          exports.isSuspense = isSuspense;
          exports.isValidElementType = isValidElementType;
          exports.typeOf = typeOf;
        })();
      }
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/react-is/index.js
  var require_react_is = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/react-is/index.js"(exports, module) {
      "use strict";
      if (false) {
        module.exports = null;
      } else {
        module.exports = require_react_is_development();
      }
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/hoist-non-react-statics/dist/hoist-non-react-statics.cjs.js
  var require_hoist_non_react_statics_cjs = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/hoist-non-react-statics/dist/hoist-non-react-statics.cjs.js"(exports, module) {
      "use strict";
      var reactIs = require_react_is();
      var REACT_STATICS = {
        childContextTypes: true,
        contextType: true,
        contextTypes: true,
        defaultProps: true,
        displayName: true,
        getDefaultProps: true,
        getDerivedStateFromError: true,
        getDerivedStateFromProps: true,
        mixins: true,
        propTypes: true,
        type: true
      };
      var KNOWN_STATICS = {
        name: true,
        length: true,
        prototype: true,
        caller: true,
        callee: true,
        arguments: true,
        arity: true
      };
      var FORWARD_REF_STATICS = {
        "$$typeof": true,
        render: true,
        defaultProps: true,
        displayName: true,
        propTypes: true
      };
      var MEMO_STATICS = {
        "$$typeof": true,
        compare: true,
        defaultProps: true,
        displayName: true,
        propTypes: true,
        type: true
      };
      var TYPE_STATICS = {};
      TYPE_STATICS[reactIs.ForwardRef] = FORWARD_REF_STATICS;
      TYPE_STATICS[reactIs.Memo] = MEMO_STATICS;
      function getStatics(component) {
        if (reactIs.isMemo(component)) {
          return MEMO_STATICS;
        }
        return TYPE_STATICS[component["$$typeof"]] || REACT_STATICS;
      }
      var defineProperty = Object.defineProperty;
      var getOwnPropertyNames = Object.getOwnPropertyNames;
      var getOwnPropertySymbols = Object.getOwnPropertySymbols;
      var getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
      var getPrototypeOf = Object.getPrototypeOf;
      var objectPrototype = Object.prototype;
      function hoistNonReactStatics2(targetComponent, sourceComponent, blacklist) {
        if (typeof sourceComponent !== "string") {
          if (objectPrototype) {
            var inheritedComponent = getPrototypeOf(sourceComponent);
            if (inheritedComponent && inheritedComponent !== objectPrototype) {
              hoistNonReactStatics2(targetComponent, inheritedComponent, blacklist);
            }
          }
          var keys = getOwnPropertyNames(sourceComponent);
          if (getOwnPropertySymbols) {
            keys = keys.concat(getOwnPropertySymbols(sourceComponent));
          }
          var targetStatics = getStatics(targetComponent);
          var sourceStatics = getStatics(sourceComponent);
          for (var i = 0; i < keys.length; ++i) {
            var key = keys[i];
            if (!KNOWN_STATICS[key] && !(blacklist && blacklist[key]) && !(sourceStatics && sourceStatics[key]) && !(targetStatics && targetStatics[key])) {
              var descriptor = getOwnPropertyDescriptor(sourceComponent, key);
              try {
                defineProperty(targetComponent, key, descriptor);
              } catch (e) {
              }
            }
          }
        }
        return targetComponent;
      }
      module.exports = hoistNonReactStatics2;
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/object-assign/index.js
  var require_object_assign = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/object-assign/index.js"(exports, module) {
      "use strict";
      var getOwnPropertySymbols = Object.getOwnPropertySymbols;
      var hasOwnProperty = Object.prototype.hasOwnProperty;
      var propIsEnumerable = Object.prototype.propertyIsEnumerable;
      function toObject(val) {
        if (val === null || val === void 0) {
          throw new TypeError("Object.assign cannot be called with null or undefined");
        }
        return Object(val);
      }
      function shouldUseNative() {
        try {
          if (!Object.assign) {
            return false;
          }
          var test1 = new String("abc");
          test1[5] = "de";
          if (Object.getOwnPropertyNames(test1)[0] === "5") {
            return false;
          }
          var test2 = {};
          for (var i = 0; i < 10; i++) {
            test2["_" + String.fromCharCode(i)] = i;
          }
          var order2 = Object.getOwnPropertyNames(test2).map(function(n) {
            return test2[n];
          });
          if (order2.join("") !== "0123456789") {
            return false;
          }
          var test3 = {};
          "abcdefghijklmnopqrst".split("").forEach(function(letter) {
            test3[letter] = letter;
          });
          if (Object.keys(Object.assign({}, test3)).join("") !== "abcdefghijklmnopqrst") {
            return false;
          }
          return true;
        } catch (err) {
          return false;
        }
      }
      module.exports = shouldUseNative() ? Object.assign : function(target, source) {
        var from;
        var to = toObject(target);
        var symbols;
        for (var s = 1; s < arguments.length; s++) {
          from = Object(arguments[s]);
          for (var key in from) {
            if (hasOwnProperty.call(from, key)) {
              to[key] = from[key];
            }
          }
          if (getOwnPropertySymbols) {
            symbols = getOwnPropertySymbols(from);
            for (var i = 0; i < symbols.length; i++) {
              if (propIsEnumerable.call(from, symbols[i])) {
                to[symbols[i]] = from[symbols[i]];
              }
            }
          }
        }
        return to;
      };
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/prop-types/lib/ReactPropTypesSecret.js
  var require_ReactPropTypesSecret = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/prop-types/lib/ReactPropTypesSecret.js"(exports, module) {
      "use strict";
      var ReactPropTypesSecret = "SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED";
      module.exports = ReactPropTypesSecret;
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/prop-types/lib/has.js
  var require_has = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/prop-types/lib/has.js"(exports, module) {
      module.exports = Function.call.bind(Object.prototype.hasOwnProperty);
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/prop-types/checkPropTypes.js
  var require_checkPropTypes = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/prop-types/checkPropTypes.js"(exports, module) {
      "use strict";
      var printWarning = function() {
      };
      if (true) {
        ReactPropTypesSecret = require_ReactPropTypesSecret();
        loggedTypeFailures = {};
        has = require_has();
        printWarning = function(text) {
          var message = "Warning: " + text;
          if (typeof console !== "undefined") {
            console.error(message);
          }
          try {
            throw new Error(message);
          } catch (x) {
          }
        };
      }
      var ReactPropTypesSecret;
      var loggedTypeFailures;
      var has;
      function checkPropTypes(typeSpecs, values, location, componentName, getStack) {
        if (true) {
          for (var typeSpecName in typeSpecs) {
            if (has(typeSpecs, typeSpecName)) {
              var error;
              try {
                if (typeof typeSpecs[typeSpecName] !== "function") {
                  var err = Error(
                    (componentName || "React class") + ": " + location + " type `" + typeSpecName + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + typeof typeSpecs[typeSpecName] + "`.This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`."
                  );
                  err.name = "Invariant Violation";
                  throw err;
                }
                error = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, ReactPropTypesSecret);
              } catch (ex) {
                error = ex;
              }
              if (error && !(error instanceof Error)) {
                printWarning(
                  (componentName || "React class") + ": type specification of " + location + " `" + typeSpecName + "` is invalid; the type checker function must return `null` or an `Error` but returned a " + typeof error + ". You may have forgotten to pass an argument to the type checker creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and shape all require an argument)."
                );
              }
              if (error instanceof Error && !(error.message in loggedTypeFailures)) {
                loggedTypeFailures[error.message] = true;
                var stack = getStack ? getStack() : "";
                printWarning(
                  "Failed " + location + " type: " + error.message + (stack != null ? stack : "")
                );
              }
            }
          }
        }
      }
      checkPropTypes.resetWarningCache = function() {
        if (true) {
          loggedTypeFailures = {};
        }
      };
      module.exports = checkPropTypes;
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/react/cjs/react.development.js
  var require_react_development = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/react/cjs/react.development.js"(exports) {
      "use strict";
      if (true) {
        (function() {
          "use strict";
          var _assign = require_object_assign();
          var checkPropTypes = require_checkPropTypes();
          var ReactVersion = "16.14.0";
          var hasSymbol = typeof Symbol === "function" && Symbol.for;
          var REACT_ELEMENT_TYPE = hasSymbol ? Symbol.for("react.element") : 60103;
          var REACT_PORTAL_TYPE = hasSymbol ? Symbol.for("react.portal") : 60106;
          var REACT_FRAGMENT_TYPE = hasSymbol ? Symbol.for("react.fragment") : 60107;
          var REACT_STRICT_MODE_TYPE = hasSymbol ? Symbol.for("react.strict_mode") : 60108;
          var REACT_PROFILER_TYPE = hasSymbol ? Symbol.for("react.profiler") : 60114;
          var REACT_PROVIDER_TYPE = hasSymbol ? Symbol.for("react.provider") : 60109;
          var REACT_CONTEXT_TYPE = hasSymbol ? Symbol.for("react.context") : 60110;
          var REACT_CONCURRENT_MODE_TYPE = hasSymbol ? Symbol.for("react.concurrent_mode") : 60111;
          var REACT_FORWARD_REF_TYPE = hasSymbol ? Symbol.for("react.forward_ref") : 60112;
          var REACT_SUSPENSE_TYPE = hasSymbol ? Symbol.for("react.suspense") : 60113;
          var REACT_SUSPENSE_LIST_TYPE = hasSymbol ? Symbol.for("react.suspense_list") : 60120;
          var REACT_MEMO_TYPE = hasSymbol ? Symbol.for("react.memo") : 60115;
          var REACT_LAZY_TYPE = hasSymbol ? Symbol.for("react.lazy") : 60116;
          var REACT_BLOCK_TYPE = hasSymbol ? Symbol.for("react.block") : 60121;
          var REACT_FUNDAMENTAL_TYPE = hasSymbol ? Symbol.for("react.fundamental") : 60117;
          var REACT_RESPONDER_TYPE = hasSymbol ? Symbol.for("react.responder") : 60118;
          var REACT_SCOPE_TYPE = hasSymbol ? Symbol.for("react.scope") : 60119;
          var MAYBE_ITERATOR_SYMBOL = typeof Symbol === "function" && Symbol.iterator;
          var FAUX_ITERATOR_SYMBOL = "@@iterator";
          function getIteratorFn(maybeIterable) {
            if (maybeIterable === null || typeof maybeIterable !== "object") {
              return null;
            }
            var maybeIterator = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL];
            if (typeof maybeIterator === "function") {
              return maybeIterator;
            }
            return null;
          }
          var ReactCurrentDispatcher = {
            /**
             * @internal
             * @type {ReactComponent}
             */
            current: null
          };
          var ReactCurrentBatchConfig = {
            suspense: null
          };
          var ReactCurrentOwner = {
            /**
             * @internal
             * @type {ReactComponent}
             */
            current: null
          };
          var BEFORE_SLASH_RE = /^(.*)[\\\/]/;
          function describeComponentFrame(name, source, ownerName) {
            var sourceInfo = "";
            if (source) {
              var path = source.fileName;
              var fileName = path.replace(BEFORE_SLASH_RE, "");
              {
                if (/^index\./.test(fileName)) {
                  var match = path.match(BEFORE_SLASH_RE);
                  if (match) {
                    var pathBeforeSlash = match[1];
                    if (pathBeforeSlash) {
                      var folderName = pathBeforeSlash.replace(BEFORE_SLASH_RE, "");
                      fileName = folderName + "/" + fileName;
                    }
                  }
                }
              }
              sourceInfo = " (at " + fileName + ":" + source.lineNumber + ")";
            } else if (ownerName) {
              sourceInfo = " (created by " + ownerName + ")";
            }
            return "\n    in " + (name || "Unknown") + sourceInfo;
          }
          var Resolved = 1;
          function refineResolvedLazyComponent(lazyComponent) {
            return lazyComponent._status === Resolved ? lazyComponent._result : null;
          }
          function getWrappedName(outerType, innerType, wrapperName) {
            var functionName = innerType.displayName || innerType.name || "";
            return outerType.displayName || (functionName !== "" ? wrapperName + "(" + functionName + ")" : wrapperName);
          }
          function getComponentName(type2) {
            if (type2 == null) {
              return null;
            }
            {
              if (typeof type2.tag === "number") {
                error("Received an unexpected object in getComponentName(). This is likely a bug in React. Please file an issue.");
              }
            }
            if (typeof type2 === "function") {
              return type2.displayName || type2.name || null;
            }
            if (typeof type2 === "string") {
              return type2;
            }
            switch (type2) {
              case REACT_FRAGMENT_TYPE:
                return "Fragment";
              case REACT_PORTAL_TYPE:
                return "Portal";
              case REACT_PROFILER_TYPE:
                return "Profiler";
              case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
              case REACT_SUSPENSE_TYPE:
                return "Suspense";
              case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            }
            if (typeof type2 === "object") {
              switch (type2.$$typeof) {
                case REACT_CONTEXT_TYPE:
                  return "Context.Consumer";
                case REACT_PROVIDER_TYPE:
                  return "Context.Provider";
                case REACT_FORWARD_REF_TYPE:
                  return getWrappedName(type2, type2.render, "ForwardRef");
                case REACT_MEMO_TYPE:
                  return getComponentName(type2.type);
                case REACT_BLOCK_TYPE:
                  return getComponentName(type2.render);
                case REACT_LAZY_TYPE: {
                  var thenable = type2;
                  var resolvedThenable = refineResolvedLazyComponent(thenable);
                  if (resolvedThenable) {
                    return getComponentName(resolvedThenable);
                  }
                  break;
                }
              }
            }
            return null;
          }
          var ReactDebugCurrentFrame = {};
          var currentlyValidatingElement = null;
          function setCurrentlyValidatingElement(element) {
            {
              currentlyValidatingElement = element;
            }
          }
          {
            ReactDebugCurrentFrame.getCurrentStack = null;
            ReactDebugCurrentFrame.getStackAddendum = function() {
              var stack = "";
              if (currentlyValidatingElement) {
                var name = getComponentName(currentlyValidatingElement.type);
                var owner = currentlyValidatingElement._owner;
                stack += describeComponentFrame(name, currentlyValidatingElement._source, owner && getComponentName(owner.type));
              }
              var impl = ReactDebugCurrentFrame.getCurrentStack;
              if (impl) {
                stack += impl() || "";
              }
              return stack;
            };
          }
          var IsSomeRendererActing = {
            current: false
          };
          var ReactSharedInternals = {
            ReactCurrentDispatcher,
            ReactCurrentBatchConfig,
            ReactCurrentOwner,
            IsSomeRendererActing,
            // Used by renderers to avoid bundling object-assign twice in UMD bundles:
            assign: _assign
          };
          {
            _assign(ReactSharedInternals, {
              // These should not be included in production.
              ReactDebugCurrentFrame,
              // Shim for React DOM 16.0.0 which still destructured (but not used) this.
              // TODO: remove in React 17.0.
              ReactComponentTreeHook: {}
            });
          }
          function warn(format) {
            {
              for (var _len = arguments.length, args = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
                args[_key - 1] = arguments[_key];
              }
              printWarning("warn", format, args);
            }
          }
          function error(format) {
            {
              for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
                args[_key2 - 1] = arguments[_key2];
              }
              printWarning("error", format, args);
            }
          }
          function printWarning(level, format, args) {
            {
              var hasExistingStack = args.length > 0 && typeof args[args.length - 1] === "string" && args[args.length - 1].indexOf("\n    in") === 0;
              if (!hasExistingStack) {
                var ReactDebugCurrentFrame2 = ReactSharedInternals.ReactDebugCurrentFrame;
                var stack = ReactDebugCurrentFrame2.getStackAddendum();
                if (stack !== "") {
                  format += "%s";
                  args = args.concat([stack]);
                }
              }
              var argsWithFormat = args.map(function(item) {
                return "" + item;
              });
              argsWithFormat.unshift("Warning: " + format);
              Function.prototype.apply.call(console[level], console, argsWithFormat);
              try {
                var argIndex = 0;
                var message = "Warning: " + format.replace(/%s/g, function() {
                  return args[argIndex++];
                });
                throw new Error(message);
              } catch (x) {
              }
            }
          }
          var didWarnStateUpdateForUnmountedComponent = {};
          function warnNoop(publicInstance, callerName) {
            {
              var _constructor = publicInstance.constructor;
              var componentName = _constructor && (_constructor.displayName || _constructor.name) || "ReactClass";
              var warningKey = componentName + "." + callerName;
              if (didWarnStateUpdateForUnmountedComponent[warningKey]) {
                return;
              }
              error("Can't call %s on a component that is not yet mounted. This is a no-op, but it might indicate a bug in your application. Instead, assign to `this.state` directly or define a `state = {};` class property with the desired state in the %s component.", callerName, componentName);
              didWarnStateUpdateForUnmountedComponent[warningKey] = true;
            }
          }
          var ReactNoopUpdateQueue = {
            /**
             * Checks whether or not this composite component is mounted.
             * @param {ReactClass} publicInstance The instance we want to test.
             * @return {boolean} True if mounted, false otherwise.
             * @protected
             * @final
             */
            isMounted: function(publicInstance) {
              return false;
            },
            /**
             * Forces an update. This should only be invoked when it is known with
             * certainty that we are **not** in a DOM transaction.
             *
             * You may want to call this when you know that some deeper aspect of the
             * component's state has changed but `setState` was not called.
             *
             * This will not invoke `shouldComponentUpdate`, but it will invoke
             * `componentWillUpdate` and `componentDidUpdate`.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {?function} callback Called after component is updated.
             * @param {?string} callerName name of the calling function in the public API.
             * @internal
             */
            enqueueForceUpdate: function(publicInstance, callback, callerName) {
              warnNoop(publicInstance, "forceUpdate");
            },
            /**
             * Replaces all of the state. Always use this or `setState` to mutate state.
             * You should treat `this.state` as immutable.
             *
             * There is no guarantee that `this.state` will be immediately updated, so
             * accessing `this.state` after calling this method may return the old value.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {object} completeState Next state.
             * @param {?function} callback Called after component is updated.
             * @param {?string} callerName name of the calling function in the public API.
             * @internal
             */
            enqueueReplaceState: function(publicInstance, completeState, callback, callerName) {
              warnNoop(publicInstance, "replaceState");
            },
            /**
             * Sets a subset of the state. This only exists because _pendingState is
             * internal. This provides a merging strategy that is not available to deep
             * properties which is confusing. TODO: Expose pendingState or don't use it
             * during the merge.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {object} partialState Next partial state to be merged with state.
             * @param {?function} callback Called after component is updated.
             * @param {?string} Name of the calling function in the public API.
             * @internal
             */
            enqueueSetState: function(publicInstance, partialState, callback, callerName) {
              warnNoop(publicInstance, "setState");
            }
          };
          var emptyObject = {};
          {
            Object.freeze(emptyObject);
          }
          function Component(props, context, updater) {
            this.props = props;
            this.context = context;
            this.refs = emptyObject;
            this.updater = updater || ReactNoopUpdateQueue;
          }
          Component.prototype.isReactComponent = {};
          Component.prototype.setState = function(partialState, callback) {
            if (!(typeof partialState === "object" || typeof partialState === "function" || partialState == null)) {
              {
                throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
              }
            }
            this.updater.enqueueSetState(this, partialState, callback, "setState");
          };
          Component.prototype.forceUpdate = function(callback) {
            this.updater.enqueueForceUpdate(this, callback, "forceUpdate");
          };
          {
            var deprecatedAPIs = {
              isMounted: ["isMounted", "Instead, make sure to clean up subscriptions and pending requests in componentWillUnmount to prevent memory leaks."],
              replaceState: ["replaceState", "Refactor your code to use setState instead (see https://github.com/facebook/react/issues/3236)."]
            };
            var defineDeprecationWarning = function(methodName, info) {
              Object.defineProperty(Component.prototype, methodName, {
                get: function() {
                  warn("%s(...) is deprecated in plain JavaScript React classes. %s", info[0], info[1]);
                  return void 0;
                }
              });
            };
            for (var fnName in deprecatedAPIs) {
              if (deprecatedAPIs.hasOwnProperty(fnName)) {
                defineDeprecationWarning(fnName, deprecatedAPIs[fnName]);
              }
            }
          }
          function ComponentDummy() {
          }
          ComponentDummy.prototype = Component.prototype;
          function PureComponent(props, context, updater) {
            this.props = props;
            this.context = context;
            this.refs = emptyObject;
            this.updater = updater || ReactNoopUpdateQueue;
          }
          var pureComponentPrototype = PureComponent.prototype = new ComponentDummy();
          pureComponentPrototype.constructor = PureComponent;
          _assign(pureComponentPrototype, Component.prototype);
          pureComponentPrototype.isPureReactComponent = true;
          function createRef() {
            var refObject = {
              current: null
            };
            {
              Object.seal(refObject);
            }
            return refObject;
          }
          var hasOwnProperty = Object.prototype.hasOwnProperty;
          var RESERVED_PROPS = {
            key: true,
            ref: true,
            __self: true,
            __source: true
          };
          var specialPropKeyWarningShown, specialPropRefWarningShown, didWarnAboutStringRefs;
          {
            didWarnAboutStringRefs = {};
          }
          function hasValidRef(config) {
            {
              if (hasOwnProperty.call(config, "ref")) {
                var getter = Object.getOwnPropertyDescriptor(config, "ref").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.ref !== void 0;
          }
          function hasValidKey(config) {
            {
              if (hasOwnProperty.call(config, "key")) {
                var getter = Object.getOwnPropertyDescriptor(config, "key").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.key !== void 0;
          }
          function defineKeyPropWarningGetter(props, displayName) {
            var warnAboutAccessingKey = function() {
              {
                if (!specialPropKeyWarningShown) {
                  specialPropKeyWarningShown = true;
                  error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://fb.me/react-special-props)", displayName);
                }
              }
            };
            warnAboutAccessingKey.isReactWarning = true;
            Object.defineProperty(props, "key", {
              get: warnAboutAccessingKey,
              configurable: true
            });
          }
          function defineRefPropWarningGetter(props, displayName) {
            var warnAboutAccessingRef = function() {
              {
                if (!specialPropRefWarningShown) {
                  specialPropRefWarningShown = true;
                  error("%s: `ref` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://fb.me/react-special-props)", displayName);
                }
              }
            };
            warnAboutAccessingRef.isReactWarning = true;
            Object.defineProperty(props, "ref", {
              get: warnAboutAccessingRef,
              configurable: true
            });
          }
          function warnIfStringRefCannotBeAutoConverted(config) {
            {
              if (typeof config.ref === "string" && ReactCurrentOwner.current && config.__self && ReactCurrentOwner.current.stateNode !== config.__self) {
                var componentName = getComponentName(ReactCurrentOwner.current.type);
                if (!didWarnAboutStringRefs[componentName]) {
                  error('Component "%s" contains the string ref "%s". Support for string refs will be removed in a future major release. This case cannot be automatically converted to an arrow function. We ask you to manually fix this case by using useRef() or createRef() instead. Learn more about using refs safely here: https://fb.me/react-strict-mode-string-ref', getComponentName(ReactCurrentOwner.current.type), config.ref);
                  didWarnAboutStringRefs[componentName] = true;
                }
              }
            }
          }
          var ReactElement = function(type2, key, ref, self2, source, owner, props) {
            var element = {
              // This tag allows us to uniquely identify this as a React Element
              $$typeof: REACT_ELEMENT_TYPE,
              // Built-in properties that belong on the element
              type: type2,
              key,
              ref,
              props,
              // Record the component responsible for creating this element.
              _owner: owner
            };
            {
              element._store = {};
              Object.defineProperty(element._store, "validated", {
                configurable: false,
                enumerable: false,
                writable: true,
                value: false
              });
              Object.defineProperty(element, "_self", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: self2
              });
              Object.defineProperty(element, "_source", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: source
              });
              if (Object.freeze) {
                Object.freeze(element.props);
                Object.freeze(element);
              }
            }
            return element;
          };
          function createElement(type2, config, children) {
            var propName;
            var props = {};
            var key = null;
            var ref = null;
            var self2 = null;
            var source = null;
            if (config != null) {
              if (hasValidRef(config)) {
                ref = config.ref;
                {
                  warnIfStringRefCannotBeAutoConverted(config);
                }
              }
              if (hasValidKey(config)) {
                key = "" + config.key;
              }
              self2 = config.__self === void 0 ? null : config.__self;
              source = config.__source === void 0 ? null : config.__source;
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  props[propName] = config[propName];
                }
              }
            }
            var childrenLength = arguments.length - 2;
            if (childrenLength === 1) {
              props.children = children;
            } else if (childrenLength > 1) {
              var childArray = Array(childrenLength);
              for (var i = 0; i < childrenLength; i++) {
                childArray[i] = arguments[i + 2];
              }
              {
                if (Object.freeze) {
                  Object.freeze(childArray);
                }
              }
              props.children = childArray;
            }
            if (type2 && type2.defaultProps) {
              var defaultProps = type2.defaultProps;
              for (propName in defaultProps) {
                if (props[propName] === void 0) {
                  props[propName] = defaultProps[propName];
                }
              }
            }
            {
              if (key || ref) {
                var displayName = typeof type2 === "function" ? type2.displayName || type2.name || "Unknown" : type2;
                if (key) {
                  defineKeyPropWarningGetter(props, displayName);
                }
                if (ref) {
                  defineRefPropWarningGetter(props, displayName);
                }
              }
            }
            return ReactElement(type2, key, ref, self2, source, ReactCurrentOwner.current, props);
          }
          function cloneAndReplaceKey(oldElement, newKey) {
            var newElement = ReactElement(oldElement.type, newKey, oldElement.ref, oldElement._self, oldElement._source, oldElement._owner, oldElement.props);
            return newElement;
          }
          function cloneElement(element, config, children) {
            if (!!(element === null || element === void 0)) {
              {
                throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + element + ".");
              }
            }
            var propName;
            var props = _assign({}, element.props);
            var key = element.key;
            var ref = element.ref;
            var self2 = element._self;
            var source = element._source;
            var owner = element._owner;
            if (config != null) {
              if (hasValidRef(config)) {
                ref = config.ref;
                owner = ReactCurrentOwner.current;
              }
              if (hasValidKey(config)) {
                key = "" + config.key;
              }
              var defaultProps;
              if (element.type && element.type.defaultProps) {
                defaultProps = element.type.defaultProps;
              }
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  if (config[propName] === void 0 && defaultProps !== void 0) {
                    props[propName] = defaultProps[propName];
                  } else {
                    props[propName] = config[propName];
                  }
                }
              }
            }
            var childrenLength = arguments.length - 2;
            if (childrenLength === 1) {
              props.children = children;
            } else if (childrenLength > 1) {
              var childArray = Array(childrenLength);
              for (var i = 0; i < childrenLength; i++) {
                childArray[i] = arguments[i + 2];
              }
              props.children = childArray;
            }
            return ReactElement(element.type, key, ref, self2, source, owner, props);
          }
          function isValidElement(object) {
            return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
          }
          var SEPARATOR = ".";
          var SUBSEPARATOR = ":";
          function escape(key) {
            var escapeRegex = /[=:]/g;
            var escaperLookup = {
              "=": "=0",
              ":": "=2"
            };
            var escapedString = ("" + key).replace(escapeRegex, function(match) {
              return escaperLookup[match];
            });
            return "$" + escapedString;
          }
          var didWarnAboutMaps = false;
          var userProvidedKeyEscapeRegex = /\/+/g;
          function escapeUserProvidedKey(text) {
            return ("" + text).replace(userProvidedKeyEscapeRegex, "$&/");
          }
          var POOL_SIZE = 10;
          var traverseContextPool = [];
          function getPooledTraverseContext(mapResult, keyPrefix, mapFunction, mapContext) {
            if (traverseContextPool.length) {
              var traverseContext = traverseContextPool.pop();
              traverseContext.result = mapResult;
              traverseContext.keyPrefix = keyPrefix;
              traverseContext.func = mapFunction;
              traverseContext.context = mapContext;
              traverseContext.count = 0;
              return traverseContext;
            } else {
              return {
                result: mapResult,
                keyPrefix,
                func: mapFunction,
                context: mapContext,
                count: 0
              };
            }
          }
          function releaseTraverseContext(traverseContext) {
            traverseContext.result = null;
            traverseContext.keyPrefix = null;
            traverseContext.func = null;
            traverseContext.context = null;
            traverseContext.count = 0;
            if (traverseContextPool.length < POOL_SIZE) {
              traverseContextPool.push(traverseContext);
            }
          }
          function traverseAllChildrenImpl(children, nameSoFar, callback, traverseContext) {
            var type2 = typeof children;
            if (type2 === "undefined" || type2 === "boolean") {
              children = null;
            }
            var invokeCallback = false;
            if (children === null) {
              invokeCallback = true;
            } else {
              switch (type2) {
                case "string":
                case "number":
                  invokeCallback = true;
                  break;
                case "object":
                  switch (children.$$typeof) {
                    case REACT_ELEMENT_TYPE:
                    case REACT_PORTAL_TYPE:
                      invokeCallback = true;
                  }
              }
            }
            if (invokeCallback) {
              callback(
                traverseContext,
                children,
                // If it's the only child, treat the name as if it was wrapped in an array
                // so that it's consistent if the number of children grows.
                nameSoFar === "" ? SEPARATOR + getComponentKey(children, 0) : nameSoFar
              );
              return 1;
            }
            var child;
            var nextName;
            var subtreeCount = 0;
            var nextNamePrefix = nameSoFar === "" ? SEPARATOR : nameSoFar + SUBSEPARATOR;
            if (Array.isArray(children)) {
              for (var i = 0; i < children.length; i++) {
                child = children[i];
                nextName = nextNamePrefix + getComponentKey(child, i);
                subtreeCount += traverseAllChildrenImpl(child, nextName, callback, traverseContext);
              }
            } else {
              var iteratorFn = getIteratorFn(children);
              if (typeof iteratorFn === "function") {
                {
                  if (iteratorFn === children.entries) {
                    if (!didWarnAboutMaps) {
                      warn("Using Maps as children is deprecated and will be removed in a future major release. Consider converting children to an array of keyed ReactElements instead.");
                    }
                    didWarnAboutMaps = true;
                  }
                }
                var iterator = iteratorFn.call(children);
                var step;
                var ii = 0;
                while (!(step = iterator.next()).done) {
                  child = step.value;
                  nextName = nextNamePrefix + getComponentKey(child, ii++);
                  subtreeCount += traverseAllChildrenImpl(child, nextName, callback, traverseContext);
                }
              } else if (type2 === "object") {
                var addendum = "";
                {
                  addendum = " If you meant to render a collection of children, use an array instead." + ReactDebugCurrentFrame.getStackAddendum();
                }
                var childrenString = "" + children;
                {
                  {
                    throw Error("Objects are not valid as a React child (found: " + (childrenString === "[object Object]" ? "object with keys {" + Object.keys(children).join(", ") + "}" : childrenString) + ")." + addendum);
                  }
                }
              }
            }
            return subtreeCount;
          }
          function traverseAllChildren(children, callback, traverseContext) {
            if (children == null) {
              return 0;
            }
            return traverseAllChildrenImpl(children, "", callback, traverseContext);
          }
          function getComponentKey(component, index) {
            if (typeof component === "object" && component !== null && component.key != null) {
              return escape(component.key);
            }
            return index.toString(36);
          }
          function forEachSingleChild(bookKeeping, child, name) {
            var func = bookKeeping.func, context = bookKeeping.context;
            func.call(context, child, bookKeeping.count++);
          }
          function forEachChildren(children, forEachFunc, forEachContext) {
            if (children == null) {
              return children;
            }
            var traverseContext = getPooledTraverseContext(null, null, forEachFunc, forEachContext);
            traverseAllChildren(children, forEachSingleChild, traverseContext);
            releaseTraverseContext(traverseContext);
          }
          function mapSingleChildIntoContext(bookKeeping, child, childKey) {
            var result = bookKeeping.result, keyPrefix = bookKeeping.keyPrefix, func = bookKeeping.func, context = bookKeeping.context;
            var mappedChild = func.call(context, child, bookKeeping.count++);
            if (Array.isArray(mappedChild)) {
              mapIntoWithKeyPrefixInternal(mappedChild, result, childKey, function(c) {
                return c;
              });
            } else if (mappedChild != null) {
              if (isValidElement(mappedChild)) {
                mappedChild = cloneAndReplaceKey(
                  mappedChild,
                  // Keep both the (mapped) and old keys if they differ, just as
                  // traverseAllChildren used to do for objects as children
                  keyPrefix + (mappedChild.key && (!child || child.key !== mappedChild.key) ? escapeUserProvidedKey(mappedChild.key) + "/" : "") + childKey
                );
              }
              result.push(mappedChild);
            }
          }
          function mapIntoWithKeyPrefixInternal(children, array, prefix, func, context) {
            var escapedPrefix = "";
            if (prefix != null) {
              escapedPrefix = escapeUserProvidedKey(prefix) + "/";
            }
            var traverseContext = getPooledTraverseContext(array, escapedPrefix, func, context);
            traverseAllChildren(children, mapSingleChildIntoContext, traverseContext);
            releaseTraverseContext(traverseContext);
          }
          function mapChildren(children, func, context) {
            if (children == null) {
              return children;
            }
            var result = [];
            mapIntoWithKeyPrefixInternal(children, result, null, func, context);
            return result;
          }
          function countChildren(children) {
            return traverseAllChildren(children, function() {
              return null;
            }, null);
          }
          function toArray(children) {
            var result = [];
            mapIntoWithKeyPrefixInternal(children, result, null, function(child) {
              return child;
            });
            return result;
          }
          function onlyChild(children) {
            if (!isValidElement(children)) {
              {
                throw Error("React.Children.only expected to receive a single React element child.");
              }
            }
            return children;
          }
          function createContext(defaultValue, calculateChangedBits) {
            if (calculateChangedBits === void 0) {
              calculateChangedBits = null;
            } else {
              {
                if (calculateChangedBits !== null && typeof calculateChangedBits !== "function") {
                  error("createContext: Expected the optional second argument to be a function. Instead received: %s", calculateChangedBits);
                }
              }
            }
            var context = {
              $$typeof: REACT_CONTEXT_TYPE,
              _calculateChangedBits: calculateChangedBits,
              // As a workaround to support multiple concurrent renderers, we categorize
              // some renderers as primary and others as secondary. We only expect
              // there to be two concurrent renderers at most: React Native (primary) and
              // Fabric (secondary); React DOM (primary) and React ART (secondary).
              // Secondary renderers store their context values on separate fields.
              _currentValue: defaultValue,
              _currentValue2: defaultValue,
              // Used to track how many concurrent renderers this context currently
              // supports within in a single renderer. Such as parallel server rendering.
              _threadCount: 0,
              // These are circular
              Provider: null,
              Consumer: null
            };
            context.Provider = {
              $$typeof: REACT_PROVIDER_TYPE,
              _context: context
            };
            var hasWarnedAboutUsingNestedContextConsumers = false;
            var hasWarnedAboutUsingConsumerProvider = false;
            {
              var Consumer = {
                $$typeof: REACT_CONTEXT_TYPE,
                _context: context,
                _calculateChangedBits: context._calculateChangedBits
              };
              Object.defineProperties(Consumer, {
                Provider: {
                  get: function() {
                    if (!hasWarnedAboutUsingConsumerProvider) {
                      hasWarnedAboutUsingConsumerProvider = true;
                      error("Rendering <Context.Consumer.Provider> is not supported and will be removed in a future major release. Did you mean to render <Context.Provider> instead?");
                    }
                    return context.Provider;
                  },
                  set: function(_Provider) {
                    context.Provider = _Provider;
                  }
                },
                _currentValue: {
                  get: function() {
                    return context._currentValue;
                  },
                  set: function(_currentValue) {
                    context._currentValue = _currentValue;
                  }
                },
                _currentValue2: {
                  get: function() {
                    return context._currentValue2;
                  },
                  set: function(_currentValue2) {
                    context._currentValue2 = _currentValue2;
                  }
                },
                _threadCount: {
                  get: function() {
                    return context._threadCount;
                  },
                  set: function(_threadCount) {
                    context._threadCount = _threadCount;
                  }
                },
                Consumer: {
                  get: function() {
                    if (!hasWarnedAboutUsingNestedContextConsumers) {
                      hasWarnedAboutUsingNestedContextConsumers = true;
                      error("Rendering <Context.Consumer.Consumer> is not supported and will be removed in a future major release. Did you mean to render <Context.Consumer> instead?");
                    }
                    return context.Consumer;
                  }
                }
              });
              context.Consumer = Consumer;
            }
            {
              context._currentRenderer = null;
              context._currentRenderer2 = null;
            }
            return context;
          }
          function lazy(ctor) {
            var lazyType = {
              $$typeof: REACT_LAZY_TYPE,
              _ctor: ctor,
              // React uses these fields to store the result.
              _status: -1,
              _result: null
            };
            {
              var defaultProps;
              var propTypes;
              Object.defineProperties(lazyType, {
                defaultProps: {
                  configurable: true,
                  get: function() {
                    return defaultProps;
                  },
                  set: function(newDefaultProps) {
                    error("React.lazy(...): It is not supported to assign `defaultProps` to a lazy component import. Either specify them where the component is defined, or create a wrapping component around it.");
                    defaultProps = newDefaultProps;
                    Object.defineProperty(lazyType, "defaultProps", {
                      enumerable: true
                    });
                  }
                },
                propTypes: {
                  configurable: true,
                  get: function() {
                    return propTypes;
                  },
                  set: function(newPropTypes) {
                    error("React.lazy(...): It is not supported to assign `propTypes` to a lazy component import. Either specify them where the component is defined, or create a wrapping component around it.");
                    propTypes = newPropTypes;
                    Object.defineProperty(lazyType, "propTypes", {
                      enumerable: true
                    });
                  }
                }
              });
            }
            return lazyType;
          }
          function forwardRef(render2) {
            {
              if (render2 != null && render2.$$typeof === REACT_MEMO_TYPE) {
                error("forwardRef requires a render function but received a `memo` component. Instead of forwardRef(memo(...)), use memo(forwardRef(...)).");
              } else if (typeof render2 !== "function") {
                error("forwardRef requires a render function but was given %s.", render2 === null ? "null" : typeof render2);
              } else {
                if (render2.length !== 0 && render2.length !== 2) {
                  error("forwardRef render functions accept exactly two parameters: props and ref. %s", render2.length === 1 ? "Did you forget to use the ref parameter?" : "Any additional parameter will be undefined.");
                }
              }
              if (render2 != null) {
                if (render2.defaultProps != null || render2.propTypes != null) {
                  error("forwardRef render functions do not support propTypes or defaultProps. Did you accidentally pass a React component?");
                }
              }
            }
            return {
              $$typeof: REACT_FORWARD_REF_TYPE,
              render: render2
            };
          }
          function isValidElementType(type2) {
            return typeof type2 === "string" || typeof type2 === "function" || // Note: its typeof might be other than 'symbol' or 'number' if it's a polyfill.
            type2 === REACT_FRAGMENT_TYPE || type2 === REACT_CONCURRENT_MODE_TYPE || type2 === REACT_PROFILER_TYPE || type2 === REACT_STRICT_MODE_TYPE || type2 === REACT_SUSPENSE_TYPE || type2 === REACT_SUSPENSE_LIST_TYPE || typeof type2 === "object" && type2 !== null && (type2.$$typeof === REACT_LAZY_TYPE || type2.$$typeof === REACT_MEMO_TYPE || type2.$$typeof === REACT_PROVIDER_TYPE || type2.$$typeof === REACT_CONTEXT_TYPE || type2.$$typeof === REACT_FORWARD_REF_TYPE || type2.$$typeof === REACT_FUNDAMENTAL_TYPE || type2.$$typeof === REACT_RESPONDER_TYPE || type2.$$typeof === REACT_SCOPE_TYPE || type2.$$typeof === REACT_BLOCK_TYPE);
          }
          function memo(type2, compare) {
            {
              if (!isValidElementType(type2)) {
                error("memo: The first argument must be a component. Instead received: %s", type2 === null ? "null" : typeof type2);
              }
            }
            return {
              $$typeof: REACT_MEMO_TYPE,
              type: type2,
              compare: compare === void 0 ? null : compare
            };
          }
          function resolveDispatcher() {
            var dispatcher = ReactCurrentDispatcher.current;
            if (!(dispatcher !== null)) {
              {
                throw Error("Invalid hook call. Hooks can only be called inside of the body of a function component. This could happen for one of the following reasons:\n1. You might have mismatching versions of React and the renderer (such as React DOM)\n2. You might be breaking the Rules of Hooks\n3. You might have more than one copy of React in the same app\nSee https://fb.me/react-invalid-hook-call for tips about how to debug and fix this problem.");
              }
            }
            return dispatcher;
          }
          function useContext(Context, unstable_observedBits) {
            var dispatcher = resolveDispatcher();
            {
              if (unstable_observedBits !== void 0) {
                error("useContext() second argument is reserved for future use in React. Passing it is not supported. You passed: %s.%s", unstable_observedBits, typeof unstable_observedBits === "number" && Array.isArray(arguments[2]) ? "\n\nDid you call array.map(useContext)? Calling Hooks inside a loop is not supported. Learn more at https://fb.me/rules-of-hooks" : "");
              }
              if (Context._context !== void 0) {
                var realContext = Context._context;
                if (realContext.Consumer === Context) {
                  error("Calling useContext(Context.Consumer) is not supported, may cause bugs, and will be removed in a future major release. Did you mean to call useContext(Context) instead?");
                } else if (realContext.Provider === Context) {
                  error("Calling useContext(Context.Provider) is not supported. Did you mean to call useContext(Context) instead?");
                }
              }
            }
            return dispatcher.useContext(Context, unstable_observedBits);
          }
          function useState(initialState) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useState(initialState);
          }
          function useReducer(reducer, initialArg, init) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useReducer(reducer, initialArg, init);
          }
          function useRef(initialValue) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useRef(initialValue);
          }
          function useEffect(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useEffect(create, deps);
          }
          function useLayoutEffect(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useLayoutEffect(create, deps);
          }
          function useCallback(callback, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useCallback(callback, deps);
          }
          function useMemo(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useMemo(create, deps);
          }
          function useImperativeHandle(ref, create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useImperativeHandle(ref, create, deps);
          }
          function useDebugValue(value, formatterFn) {
            {
              var dispatcher = resolveDispatcher();
              return dispatcher.useDebugValue(value, formatterFn);
            }
          }
          var propTypesMisspellWarningShown;
          {
            propTypesMisspellWarningShown = false;
          }
          function getDeclarationErrorAddendum() {
            if (ReactCurrentOwner.current) {
              var name = getComponentName(ReactCurrentOwner.current.type);
              if (name) {
                return "\n\nCheck the render method of `" + name + "`.";
              }
            }
            return "";
          }
          function getSourceInfoErrorAddendum(source) {
            if (source !== void 0) {
              var fileName = source.fileName.replace(/^.*[\\\/]/, "");
              var lineNumber = source.lineNumber;
              return "\n\nCheck your code at " + fileName + ":" + lineNumber + ".";
            }
            return "";
          }
          function getSourceInfoErrorAddendumForProps(elementProps) {
            if (elementProps !== null && elementProps !== void 0) {
              return getSourceInfoErrorAddendum(elementProps.__source);
            }
            return "";
          }
          var ownerHasKeyUseWarning = {};
          function getCurrentComponentErrorInfo(parentType) {
            var info = getDeclarationErrorAddendum();
            if (!info) {
              var parentName = typeof parentType === "string" ? parentType : parentType.displayName || parentType.name;
              if (parentName) {
                info = "\n\nCheck the top-level render call using <" + parentName + ">.";
              }
            }
            return info;
          }
          function validateExplicitKey(element, parentType) {
            if (!element._store || element._store.validated || element.key != null) {
              return;
            }
            element._store.validated = true;
            var currentComponentErrorInfo = getCurrentComponentErrorInfo(parentType);
            if (ownerHasKeyUseWarning[currentComponentErrorInfo]) {
              return;
            }
            ownerHasKeyUseWarning[currentComponentErrorInfo] = true;
            var childOwner = "";
            if (element && element._owner && element._owner !== ReactCurrentOwner.current) {
              childOwner = " It was passed a child from " + getComponentName(element._owner.type) + ".";
            }
            setCurrentlyValidatingElement(element);
            {
              error('Each child in a list should have a unique "key" prop.%s%s See https://fb.me/react-warning-keys for more information.', currentComponentErrorInfo, childOwner);
            }
            setCurrentlyValidatingElement(null);
          }
          function validateChildKeys(node, parentType) {
            if (typeof node !== "object") {
              return;
            }
            if (Array.isArray(node)) {
              for (var i = 0; i < node.length; i++) {
                var child = node[i];
                if (isValidElement(child)) {
                  validateExplicitKey(child, parentType);
                }
              }
            } else if (isValidElement(node)) {
              if (node._store) {
                node._store.validated = true;
              }
            } else if (node) {
              var iteratorFn = getIteratorFn(node);
              if (typeof iteratorFn === "function") {
                if (iteratorFn !== node.entries) {
                  var iterator = iteratorFn.call(node);
                  var step;
                  while (!(step = iterator.next()).done) {
                    if (isValidElement(step.value)) {
                      validateExplicitKey(step.value, parentType);
                    }
                  }
                }
              }
            }
          }
          function validatePropTypes(element) {
            {
              var type2 = element.type;
              if (type2 === null || type2 === void 0 || typeof type2 === "string") {
                return;
              }
              var name = getComponentName(type2);
              var propTypes;
              if (typeof type2 === "function") {
                propTypes = type2.propTypes;
              } else if (typeof type2 === "object" && (type2.$$typeof === REACT_FORWARD_REF_TYPE || // Note: Memo only checks outer props here.
              // Inner props are checked in the reconciler.
              type2.$$typeof === REACT_MEMO_TYPE)) {
                propTypes = type2.propTypes;
              } else {
                return;
              }
              if (propTypes) {
                setCurrentlyValidatingElement(element);
                checkPropTypes(propTypes, element.props, "prop", name, ReactDebugCurrentFrame.getStackAddendum);
                setCurrentlyValidatingElement(null);
              } else if (type2.PropTypes !== void 0 && !propTypesMisspellWarningShown) {
                propTypesMisspellWarningShown = true;
                error("Component %s declared `PropTypes` instead of `propTypes`. Did you misspell the property assignment?", name || "Unknown");
              }
              if (typeof type2.getDefaultProps === "function" && !type2.getDefaultProps.isReactClassApproved) {
                error("getDefaultProps is only used on classic React.createClass definitions. Use a static property named `defaultProps` instead.");
              }
            }
          }
          function validateFragmentProps(fragment) {
            {
              setCurrentlyValidatingElement(fragment);
              var keys = Object.keys(fragment.props);
              for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                if (key !== "children" && key !== "key") {
                  error("Invalid prop `%s` supplied to `React.Fragment`. React.Fragment can only have `key` and `children` props.", key);
                  break;
                }
              }
              if (fragment.ref !== null) {
                error("Invalid attribute `ref` supplied to `React.Fragment`.");
              }
              setCurrentlyValidatingElement(null);
            }
          }
          function createElementWithValidation(type2, props, children) {
            var validType = isValidElementType(type2);
            if (!validType) {
              var info = "";
              if (type2 === void 0 || typeof type2 === "object" && type2 !== null && Object.keys(type2).length === 0) {
                info += " You likely forgot to export your component from the file it's defined in, or you might have mixed up default and named imports.";
              }
              var sourceInfo = getSourceInfoErrorAddendumForProps(props);
              if (sourceInfo) {
                info += sourceInfo;
              } else {
                info += getDeclarationErrorAddendum();
              }
              var typeString;
              if (type2 === null) {
                typeString = "null";
              } else if (Array.isArray(type2)) {
                typeString = "array";
              } else if (type2 !== void 0 && type2.$$typeof === REACT_ELEMENT_TYPE) {
                typeString = "<" + (getComponentName(type2.type) || "Unknown") + " />";
                info = " Did you accidentally export a JSX literal instead of a component?";
              } else {
                typeString = typeof type2;
              }
              {
                error("React.createElement: type is invalid -- expected a string (for built-in components) or a class/function (for composite components) but got: %s.%s", typeString, info);
              }
            }
            var element = createElement.apply(this, arguments);
            if (element == null) {
              return element;
            }
            if (validType) {
              for (var i = 2; i < arguments.length; i++) {
                validateChildKeys(arguments[i], type2);
              }
            }
            if (type2 === REACT_FRAGMENT_TYPE) {
              validateFragmentProps(element);
            } else {
              validatePropTypes(element);
            }
            return element;
          }
          var didWarnAboutDeprecatedCreateFactory = false;
          function createFactoryWithValidation(type2) {
            var validatedFactory = createElementWithValidation.bind(null, type2);
            validatedFactory.type = type2;
            {
              if (!didWarnAboutDeprecatedCreateFactory) {
                didWarnAboutDeprecatedCreateFactory = true;
                warn("React.createFactory() is deprecated and will be removed in a future major release. Consider using JSX or use React.createElement() directly instead.");
              }
              Object.defineProperty(validatedFactory, "type", {
                enumerable: false,
                get: function() {
                  warn("Factory.type is deprecated. Access the class directly before passing it to createFactory.");
                  Object.defineProperty(this, "type", {
                    value: type2
                  });
                  return type2;
                }
              });
            }
            return validatedFactory;
          }
          function cloneElementWithValidation(element, props, children) {
            var newElement = cloneElement.apply(this, arguments);
            for (var i = 2; i < arguments.length; i++) {
              validateChildKeys(arguments[i], newElement.type);
            }
            validatePropTypes(newElement);
            return newElement;
          }
          {
            try {
              var frozenObject = Object.freeze({});
              var testMap = /* @__PURE__ */ new Map([[frozenObject, null]]);
              var testSet = /* @__PURE__ */ new Set([frozenObject]);
              testMap.set(0, 0);
              testSet.add(0);
            } catch (e) {
            }
          }
          var createElement$1 = createElementWithValidation;
          var cloneElement$1 = cloneElementWithValidation;
          var createFactory = createFactoryWithValidation;
          var Children = {
            map: mapChildren,
            forEach: forEachChildren,
            count: countChildren,
            toArray,
            only: onlyChild
          };
          exports.Children = Children;
          exports.Component = Component;
          exports.Fragment = REACT_FRAGMENT_TYPE;
          exports.Profiler = REACT_PROFILER_TYPE;
          exports.PureComponent = PureComponent;
          exports.StrictMode = REACT_STRICT_MODE_TYPE;
          exports.Suspense = REACT_SUSPENSE_TYPE;
          exports.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = ReactSharedInternals;
          exports.cloneElement = cloneElement$1;
          exports.createContext = createContext;
          exports.createElement = createElement$1;
          exports.createFactory = createFactory;
          exports.createRef = createRef;
          exports.forwardRef = forwardRef;
          exports.isValidElement = isValidElement;
          exports.lazy = lazy;
          exports.memo = memo;
          exports.useCallback = useCallback;
          exports.useContext = useContext;
          exports.useDebugValue = useDebugValue;
          exports.useEffect = useEffect;
          exports.useImperativeHandle = useImperativeHandle;
          exports.useLayoutEffect = useLayoutEffect;
          exports.useMemo = useMemo;
          exports.useReducer = useReducer;
          exports.useRef = useRef;
          exports.useState = useState;
          exports.version = ReactVersion;
        })();
      }
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/react/index.js
  var require_react = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/react/index.js"(exports, module) {
      "use strict";
      if (false) {
        module.exports = null;
      } else {
        module.exports = require_react_development();
      }
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/leaflet/dist/leaflet-src.js
  var require_leaflet_src = __commonJS({
    "../../../../../tmp/agrolattice_component_build/node_modules/leaflet/dist/leaflet-src.js"(exports, module) {
      (function(global, factory) {
        typeof exports === "object" && typeof module !== "undefined" ? factory(exports) : typeof define === "function" && define.amd ? define(["exports"], factory) : (global = typeof globalThis !== "undefined" ? globalThis : global || self, factory(global.leaflet = {}));
      })(exports, function(exports2) {
        "use strict";
        var version = "1.9.4";
        function extend(dest) {
          var i, j, len, src;
          for (j = 1, len = arguments.length; j < len; j++) {
            src = arguments[j];
            for (i in src) {
              dest[i] = src[i];
            }
          }
          return dest;
        }
        var create$2 = Object.create || /* @__PURE__ */ function() {
          function F() {
          }
          return function(proto) {
            F.prototype = proto;
            return new F();
          };
        }();
        function bind(fn, obj) {
          var slice = Array.prototype.slice;
          if (fn.bind) {
            return fn.bind.apply(fn, slice.call(arguments, 1));
          }
          var args = slice.call(arguments, 2);
          return function() {
            return fn.apply(obj, args.length ? args.concat(slice.call(arguments)) : arguments);
          };
        }
        var lastId = 0;
        function stamp(obj) {
          if (!("_leaflet_id" in obj)) {
            obj["_leaflet_id"] = ++lastId;
          }
          return obj._leaflet_id;
        }
        function throttle(fn, time, context) {
          var lock, args, wrapperFn, later;
          later = function() {
            lock = false;
            if (args) {
              wrapperFn.apply(context, args);
              args = false;
            }
          };
          wrapperFn = function() {
            if (lock) {
              args = arguments;
            } else {
              fn.apply(context, arguments);
              setTimeout(later, time);
              lock = true;
            }
          };
          return wrapperFn;
        }
        function wrapNum(x, range, includeMax) {
          var max = range[1], min = range[0], d = max - min;
          return x === max && includeMax ? x : ((x - min) % d + d) % d + min;
        }
        function falseFn() {
          return false;
        }
        function formatNum(num, precision) {
          if (precision === false) {
            return num;
          }
          var pow = Math.pow(10, precision === void 0 ? 6 : precision);
          return Math.round(num * pow) / pow;
        }
        function trim(str) {
          return str.trim ? str.trim() : str.replace(/^\s+|\s+$/g, "");
        }
        function splitWords(str) {
          return trim(str).split(/\s+/);
        }
        function setOptions(obj, options) {
          if (!Object.prototype.hasOwnProperty.call(obj, "options")) {
            obj.options = obj.options ? create$2(obj.options) : {};
          }
          for (var i in options) {
            obj.options[i] = options[i];
          }
          return obj.options;
        }
        function getParamString(obj, existingUrl, uppercase) {
          var params = [];
          for (var i in obj) {
            params.push(encodeURIComponent(uppercase ? i.toUpperCase() : i) + "=" + encodeURIComponent(obj[i]));
          }
          return (!existingUrl || existingUrl.indexOf("?") === -1 ? "?" : "&") + params.join("&");
        }
        var templateRe = /\{ *([\w_ -]+) *\}/g;
        function template(str, data) {
          return str.replace(templateRe, function(str2, key) {
            var value = data[key];
            if (value === void 0) {
              throw new Error("No value provided for variable " + str2);
            } else if (typeof value === "function") {
              value = value(data);
            }
            return value;
          });
        }
        var isArray = Array.isArray || function(obj) {
          return Object.prototype.toString.call(obj) === "[object Array]";
        };
        function indexOf(array, el) {
          for (var i = 0; i < array.length; i++) {
            if (array[i] === el) {
              return i;
            }
          }
          return -1;
        }
        var emptyImageUrl = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=";
        function getPrefixed(name) {
          return window["webkit" + name] || window["moz" + name] || window["ms" + name];
        }
        var lastTime = 0;
        function timeoutDefer(fn) {
          var time = +/* @__PURE__ */ new Date(), timeToCall = Math.max(0, 16 - (time - lastTime));
          lastTime = time + timeToCall;
          return window.setTimeout(fn, timeToCall);
        }
        var requestFn = window.requestAnimationFrame || getPrefixed("RequestAnimationFrame") || timeoutDefer;
        var cancelFn = window.cancelAnimationFrame || getPrefixed("CancelAnimationFrame") || getPrefixed("CancelRequestAnimationFrame") || function(id) {
          window.clearTimeout(id);
        };
        function requestAnimFrame(fn, context, immediate) {
          if (immediate && requestFn === timeoutDefer) {
            fn.call(context);
          } else {
            return requestFn.call(window, bind(fn, context));
          }
        }
        function cancelAnimFrame(id) {
          if (id) {
            cancelFn.call(window, id);
          }
        }
        var Util = {
          __proto__: null,
          extend,
          create: create$2,
          bind,
          get lastId() {
            return lastId;
          },
          stamp,
          throttle,
          wrapNum,
          falseFn,
          formatNum,
          trim,
          splitWords,
          setOptions,
          getParamString,
          template,
          isArray,
          indexOf,
          emptyImageUrl,
          requestFn,
          cancelFn,
          requestAnimFrame,
          cancelAnimFrame
        };
        function Class() {
        }
        Class.extend = function(props) {
          var NewClass = function() {
            setOptions(this);
            if (this.initialize) {
              this.initialize.apply(this, arguments);
            }
            this.callInitHooks();
          };
          var parentProto = NewClass.__super__ = this.prototype;
          var proto = create$2(parentProto);
          proto.constructor = NewClass;
          NewClass.prototype = proto;
          for (var i in this) {
            if (Object.prototype.hasOwnProperty.call(this, i) && i !== "prototype" && i !== "__super__") {
              NewClass[i] = this[i];
            }
          }
          if (props.statics) {
            extend(NewClass, props.statics);
          }
          if (props.includes) {
            checkDeprecatedMixinEvents(props.includes);
            extend.apply(null, [proto].concat(props.includes));
          }
          extend(proto, props);
          delete proto.statics;
          delete proto.includes;
          if (proto.options) {
            proto.options = parentProto.options ? create$2(parentProto.options) : {};
            extend(proto.options, props.options);
          }
          proto._initHooks = [];
          proto.callInitHooks = function() {
            if (this._initHooksCalled) {
              return;
            }
            if (parentProto.callInitHooks) {
              parentProto.callInitHooks.call(this);
            }
            this._initHooksCalled = true;
            for (var i2 = 0, len = proto._initHooks.length; i2 < len; i2++) {
              proto._initHooks[i2].call(this);
            }
          };
          return NewClass;
        };
        Class.include = function(props) {
          var parentOptions = this.prototype.options;
          extend(this.prototype, props);
          if (props.options) {
            this.prototype.options = parentOptions;
            this.mergeOptions(props.options);
          }
          return this;
        };
        Class.mergeOptions = function(options) {
          extend(this.prototype.options, options);
          return this;
        };
        Class.addInitHook = function(fn) {
          var args = Array.prototype.slice.call(arguments, 1);
          var init = typeof fn === "function" ? fn : function() {
            this[fn].apply(this, args);
          };
          this.prototype._initHooks = this.prototype._initHooks || [];
          this.prototype._initHooks.push(init);
          return this;
        };
        function checkDeprecatedMixinEvents(includes) {
          if (typeof L === "undefined" || !L || !L.Mixin) {
            return;
          }
          includes = isArray(includes) ? includes : [includes];
          for (var i = 0; i < includes.length; i++) {
            if (includes[i] === L.Mixin.Events) {
              console.warn("Deprecated include of L.Mixin.Events: this property will be removed in future releases, please inherit from L.Evented instead.", new Error().stack);
            }
          }
        }
        var Events = {
          /* @method on(type: String, fn: Function, context?: Object): this
           * Adds a listener function (`fn`) to a particular event type of the object. You can optionally specify the context of the listener (object the this keyword will point to). You can also pass several space-separated types (e.g. `'click dblclick'`).
           *
           * @alternative
           * @method on(eventMap: Object): this
           * Adds a set of type/listener pairs, e.g. `{click: onClick, mousemove: onMouseMove}`
           */
          on: function(types, fn, context) {
            if (typeof types === "object") {
              for (var type2 in types) {
                this._on(type2, types[type2], fn);
              }
            } else {
              types = splitWords(types);
              for (var i = 0, len = types.length; i < len; i++) {
                this._on(types[i], fn, context);
              }
            }
            return this;
          },
          /* @method off(type: String, fn?: Function, context?: Object): this
           * Removes a previously added listener function. If no function is specified, it will remove all the listeners of that particular event from the object. Note that if you passed a custom context to `on`, you must pass the same context to `off` in order to remove the listener.
           *
           * @alternative
           * @method off(eventMap: Object): this
           * Removes a set of type/listener pairs.
           *
           * @alternative
           * @method off: this
           * Removes all listeners to all events on the object. This includes implicitly attached events.
           */
          off: function(types, fn, context) {
            if (!arguments.length) {
              delete this._events;
            } else if (typeof types === "object") {
              for (var type2 in types) {
                this._off(type2, types[type2], fn);
              }
            } else {
              types = splitWords(types);
              var removeAll = arguments.length === 1;
              for (var i = 0, len = types.length; i < len; i++) {
                if (removeAll) {
                  this._off(types[i]);
                } else {
                  this._off(types[i], fn, context);
                }
              }
            }
            return this;
          },
          // attach listener (without syntactic sugar now)
          _on: function(type2, fn, context, _once) {
            if (typeof fn !== "function") {
              console.warn("wrong listener type: " + typeof fn);
              return;
            }
            if (this._listens(type2, fn, context) !== false) {
              return;
            }
            if (context === this) {
              context = void 0;
            }
            var newListener = { fn, ctx: context };
            if (_once) {
              newListener.once = true;
            }
            this._events = this._events || {};
            this._events[type2] = this._events[type2] || [];
            this._events[type2].push(newListener);
          },
          _off: function(type2, fn, context) {
            var listeners, i, len;
            if (!this._events) {
              return;
            }
            listeners = this._events[type2];
            if (!listeners) {
              return;
            }
            if (arguments.length === 1) {
              if (this._firingCount) {
                for (i = 0, len = listeners.length; i < len; i++) {
                  listeners[i].fn = falseFn;
                }
              }
              delete this._events[type2];
              return;
            }
            if (typeof fn !== "function") {
              console.warn("wrong listener type: " + typeof fn);
              return;
            }
            var index2 = this._listens(type2, fn, context);
            if (index2 !== false) {
              var listener = listeners[index2];
              if (this._firingCount) {
                listener.fn = falseFn;
                this._events[type2] = listeners = listeners.slice();
              }
              listeners.splice(index2, 1);
            }
          },
          // @method fire(type: String, data?: Object, propagate?: Boolean): this
          // Fires an event of the specified type. You can optionally provide a data
          // object — the first argument of the listener function will contain its
          // properties. The event can optionally be propagated to event parents.
          fire: function(type2, data, propagate) {
            if (!this.listens(type2, propagate)) {
              return this;
            }
            var event = extend({}, data, {
              type: type2,
              target: this,
              sourceTarget: data && data.sourceTarget || this
            });
            if (this._events) {
              var listeners = this._events[type2];
              if (listeners) {
                this._firingCount = this._firingCount + 1 || 1;
                for (var i = 0, len = listeners.length; i < len; i++) {
                  var l = listeners[i];
                  var fn = l.fn;
                  if (l.once) {
                    this.off(type2, fn, l.ctx);
                  }
                  fn.call(l.ctx || this, event);
                }
                this._firingCount--;
              }
            }
            if (propagate) {
              this._propagateEvent(event);
            }
            return this;
          },
          // @method listens(type: String, propagate?: Boolean): Boolean
          // @method listens(type: String, fn: Function, context?: Object, propagate?: Boolean): Boolean
          // Returns `true` if a particular event type has any listeners attached to it.
          // The verification can optionally be propagated, it will return `true` if parents have the listener attached to it.
          listens: function(type2, fn, context, propagate) {
            if (typeof type2 !== "string") {
              console.warn('"string" type argument expected');
            }
            var _fn = fn;
            if (typeof fn !== "function") {
              propagate = !!fn;
              _fn = void 0;
              context = void 0;
            }
            var listeners = this._events && this._events[type2];
            if (listeners && listeners.length) {
              if (this._listens(type2, _fn, context) !== false) {
                return true;
              }
            }
            if (propagate) {
              for (var id in this._eventParents) {
                if (this._eventParents[id].listens(type2, fn, context, propagate)) {
                  return true;
                }
              }
            }
            return false;
          },
          // returns the index (number) or false
          _listens: function(type2, fn, context) {
            if (!this._events) {
              return false;
            }
            var listeners = this._events[type2] || [];
            if (!fn) {
              return !!listeners.length;
            }
            if (context === this) {
              context = void 0;
            }
            for (var i = 0, len = listeners.length; i < len; i++) {
              if (listeners[i].fn === fn && listeners[i].ctx === context) {
                return i;
              }
            }
            return false;
          },
          // @method once(…): this
          // Behaves as [`on(…)`](#evented-on), except the listener will only get fired once and then removed.
          once: function(types, fn, context) {
            if (typeof types === "object") {
              for (var type2 in types) {
                this._on(type2, types[type2], fn, true);
              }
            } else {
              types = splitWords(types);
              for (var i = 0, len = types.length; i < len; i++) {
                this._on(types[i], fn, context, true);
              }
            }
            return this;
          },
          // @method addEventParent(obj: Evented): this
          // Adds an event parent - an `Evented` that will receive propagated events
          addEventParent: function(obj) {
            this._eventParents = this._eventParents || {};
            this._eventParents[stamp(obj)] = obj;
            return this;
          },
          // @method removeEventParent(obj: Evented): this
          // Removes an event parent, so it will stop receiving propagated events
          removeEventParent: function(obj) {
            if (this._eventParents) {
              delete this._eventParents[stamp(obj)];
            }
            return this;
          },
          _propagateEvent: function(e) {
            for (var id in this._eventParents) {
              this._eventParents[id].fire(e.type, extend({
                layer: e.target,
                propagatedFrom: e.target
              }, e), true);
            }
          }
        };
        Events.addEventListener = Events.on;
        Events.removeEventListener = Events.clearAllEventListeners = Events.off;
        Events.addOneTimeEventListener = Events.once;
        Events.fireEvent = Events.fire;
        Events.hasEventListeners = Events.listens;
        var Evented = Class.extend(Events);
        function Point(x, y, round) {
          this.x = round ? Math.round(x) : x;
          this.y = round ? Math.round(y) : y;
        }
        var trunc = Math.trunc || function(v) {
          return v > 0 ? Math.floor(v) : Math.ceil(v);
        };
        Point.prototype = {
          // @method clone(): Point
          // Returns a copy of the current point.
          clone: function() {
            return new Point(this.x, this.y);
          },
          // @method add(otherPoint: Point): Point
          // Returns the result of addition of the current and the given points.
          add: function(point) {
            return this.clone()._add(toPoint(point));
          },
          _add: function(point) {
            this.x += point.x;
            this.y += point.y;
            return this;
          },
          // @method subtract(otherPoint: Point): Point
          // Returns the result of subtraction of the given point from the current.
          subtract: function(point) {
            return this.clone()._subtract(toPoint(point));
          },
          _subtract: function(point) {
            this.x -= point.x;
            this.y -= point.y;
            return this;
          },
          // @method divideBy(num: Number): Point
          // Returns the result of division of the current point by the given number.
          divideBy: function(num) {
            return this.clone()._divideBy(num);
          },
          _divideBy: function(num) {
            this.x /= num;
            this.y /= num;
            return this;
          },
          // @method multiplyBy(num: Number): Point
          // Returns the result of multiplication of the current point by the given number.
          multiplyBy: function(num) {
            return this.clone()._multiplyBy(num);
          },
          _multiplyBy: function(num) {
            this.x *= num;
            this.y *= num;
            return this;
          },
          // @method scaleBy(scale: Point): Point
          // Multiply each coordinate of the current point by each coordinate of
          // `scale`. In linear algebra terms, multiply the point by the
          // [scaling matrix](https://en.wikipedia.org/wiki/Scaling_%28geometry%29#Matrix_representation)
          // defined by `scale`.
          scaleBy: function(point) {
            return new Point(this.x * point.x, this.y * point.y);
          },
          // @method unscaleBy(scale: Point): Point
          // Inverse of `scaleBy`. Divide each coordinate of the current point by
          // each coordinate of `scale`.
          unscaleBy: function(point) {
            return new Point(this.x / point.x, this.y / point.y);
          },
          // @method round(): Point
          // Returns a copy of the current point with rounded coordinates.
          round: function() {
            return this.clone()._round();
          },
          _round: function() {
            this.x = Math.round(this.x);
            this.y = Math.round(this.y);
            return this;
          },
          // @method floor(): Point
          // Returns a copy of the current point with floored coordinates (rounded down).
          floor: function() {
            return this.clone()._floor();
          },
          _floor: function() {
            this.x = Math.floor(this.x);
            this.y = Math.floor(this.y);
            return this;
          },
          // @method ceil(): Point
          // Returns a copy of the current point with ceiled coordinates (rounded up).
          ceil: function() {
            return this.clone()._ceil();
          },
          _ceil: function() {
            this.x = Math.ceil(this.x);
            this.y = Math.ceil(this.y);
            return this;
          },
          // @method trunc(): Point
          // Returns a copy of the current point with truncated coordinates (rounded towards zero).
          trunc: function() {
            return this.clone()._trunc();
          },
          _trunc: function() {
            this.x = trunc(this.x);
            this.y = trunc(this.y);
            return this;
          },
          // @method distanceTo(otherPoint: Point): Number
          // Returns the cartesian distance between the current and the given points.
          distanceTo: function(point) {
            point = toPoint(point);
            var x = point.x - this.x, y = point.y - this.y;
            return Math.sqrt(x * x + y * y);
          },
          // @method equals(otherPoint: Point): Boolean
          // Returns `true` if the given point has the same coordinates.
          equals: function(point) {
            point = toPoint(point);
            return point.x === this.x && point.y === this.y;
          },
          // @method contains(otherPoint: Point): Boolean
          // Returns `true` if both coordinates of the given point are less than the corresponding current point coordinates (in absolute values).
          contains: function(point) {
            point = toPoint(point);
            return Math.abs(point.x) <= Math.abs(this.x) && Math.abs(point.y) <= Math.abs(this.y);
          },
          // @method toString(): String
          // Returns a string representation of the point for debugging purposes.
          toString: function() {
            return "Point(" + formatNum(this.x) + ", " + formatNum(this.y) + ")";
          }
        };
        function toPoint(x, y, round) {
          if (x instanceof Point) {
            return x;
          }
          if (isArray(x)) {
            return new Point(x[0], x[1]);
          }
          if (x === void 0 || x === null) {
            return x;
          }
          if (typeof x === "object" && "x" in x && "y" in x) {
            return new Point(x.x, x.y);
          }
          return new Point(x, y, round);
        }
        function Bounds(a, b) {
          if (!a) {
            return;
          }
          var points = b ? [a, b] : a;
          for (var i = 0, len = points.length; i < len; i++) {
            this.extend(points[i]);
          }
        }
        Bounds.prototype = {
          // @method extend(point: Point): this
          // Extends the bounds to contain the given point.
          // @alternative
          // @method extend(otherBounds: Bounds): this
          // Extend the bounds to contain the given bounds
          extend: function(obj) {
            var min2, max2;
            if (!obj) {
              return this;
            }
            if (obj instanceof Point || typeof obj[0] === "number" || "x" in obj) {
              min2 = max2 = toPoint(obj);
            } else {
              obj = toBounds(obj);
              min2 = obj.min;
              max2 = obj.max;
              if (!min2 || !max2) {
                return this;
              }
            }
            if (!this.min && !this.max) {
              this.min = min2.clone();
              this.max = max2.clone();
            } else {
              this.min.x = Math.min(min2.x, this.min.x);
              this.max.x = Math.max(max2.x, this.max.x);
              this.min.y = Math.min(min2.y, this.min.y);
              this.max.y = Math.max(max2.y, this.max.y);
            }
            return this;
          },
          // @method getCenter(round?: Boolean): Point
          // Returns the center point of the bounds.
          getCenter: function(round) {
            return toPoint(
              (this.min.x + this.max.x) / 2,
              (this.min.y + this.max.y) / 2,
              round
            );
          },
          // @method getBottomLeft(): Point
          // Returns the bottom-left point of the bounds.
          getBottomLeft: function() {
            return toPoint(this.min.x, this.max.y);
          },
          // @method getTopRight(): Point
          // Returns the top-right point of the bounds.
          getTopRight: function() {
            return toPoint(this.max.x, this.min.y);
          },
          // @method getTopLeft(): Point
          // Returns the top-left point of the bounds (i.e. [`this.min`](#bounds-min)).
          getTopLeft: function() {
            return this.min;
          },
          // @method getBottomRight(): Point
          // Returns the bottom-right point of the bounds (i.e. [`this.max`](#bounds-max)).
          getBottomRight: function() {
            return this.max;
          },
          // @method getSize(): Point
          // Returns the size of the given bounds
          getSize: function() {
            return this.max.subtract(this.min);
          },
          // @method contains(otherBounds: Bounds): Boolean
          // Returns `true` if the rectangle contains the given one.
          // @alternative
          // @method contains(point: Point): Boolean
          // Returns `true` if the rectangle contains the given point.
          contains: function(obj) {
            var min, max;
            if (typeof obj[0] === "number" || obj instanceof Point) {
              obj = toPoint(obj);
            } else {
              obj = toBounds(obj);
            }
            if (obj instanceof Bounds) {
              min = obj.min;
              max = obj.max;
            } else {
              min = max = obj;
            }
            return min.x >= this.min.x && max.x <= this.max.x && min.y >= this.min.y && max.y <= this.max.y;
          },
          // @method intersects(otherBounds: Bounds): Boolean
          // Returns `true` if the rectangle intersects the given bounds. Two bounds
          // intersect if they have at least one point in common.
          intersects: function(bounds) {
            bounds = toBounds(bounds);
            var min = this.min, max = this.max, min2 = bounds.min, max2 = bounds.max, xIntersects = max2.x >= min.x && min2.x <= max.x, yIntersects = max2.y >= min.y && min2.y <= max.y;
            return xIntersects && yIntersects;
          },
          // @method overlaps(otherBounds: Bounds): Boolean
          // Returns `true` if the rectangle overlaps the given bounds. Two bounds
          // overlap if their intersection is an area.
          overlaps: function(bounds) {
            bounds = toBounds(bounds);
            var min = this.min, max = this.max, min2 = bounds.min, max2 = bounds.max, xOverlaps = max2.x > min.x && min2.x < max.x, yOverlaps = max2.y > min.y && min2.y < max.y;
            return xOverlaps && yOverlaps;
          },
          // @method isValid(): Boolean
          // Returns `true` if the bounds are properly initialized.
          isValid: function() {
            return !!(this.min && this.max);
          },
          // @method pad(bufferRatio: Number): Bounds
          // Returns bounds created by extending or retracting the current bounds by a given ratio in each direction.
          // For example, a ratio of 0.5 extends the bounds by 50% in each direction.
          // Negative values will retract the bounds.
          pad: function(bufferRatio) {
            var min = this.min, max = this.max, heightBuffer = Math.abs(min.x - max.x) * bufferRatio, widthBuffer = Math.abs(min.y - max.y) * bufferRatio;
            return toBounds(
              toPoint(min.x - heightBuffer, min.y - widthBuffer),
              toPoint(max.x + heightBuffer, max.y + widthBuffer)
            );
          },
          // @method equals(otherBounds: Bounds): Boolean
          // Returns `true` if the rectangle is equivalent to the given bounds.
          equals: function(bounds) {
            if (!bounds) {
              return false;
            }
            bounds = toBounds(bounds);
            return this.min.equals(bounds.getTopLeft()) && this.max.equals(bounds.getBottomRight());
          }
        };
        function toBounds(a, b) {
          if (!a || a instanceof Bounds) {
            return a;
          }
          return new Bounds(a, b);
        }
        function LatLngBounds(corner1, corner2) {
          if (!corner1) {
            return;
          }
          var latlngs = corner2 ? [corner1, corner2] : corner1;
          for (var i = 0, len = latlngs.length; i < len; i++) {
            this.extend(latlngs[i]);
          }
        }
        LatLngBounds.prototype = {
          // @method extend(latlng: LatLng): this
          // Extend the bounds to contain the given point
          // @alternative
          // @method extend(otherBounds: LatLngBounds): this
          // Extend the bounds to contain the given bounds
          extend: function(obj) {
            var sw = this._southWest, ne = this._northEast, sw2, ne2;
            if (obj instanceof LatLng) {
              sw2 = obj;
              ne2 = obj;
            } else if (obj instanceof LatLngBounds) {
              sw2 = obj._southWest;
              ne2 = obj._northEast;
              if (!sw2 || !ne2) {
                return this;
              }
            } else {
              return obj ? this.extend(toLatLng(obj) || toLatLngBounds(obj)) : this;
            }
            if (!sw && !ne) {
              this._southWest = new LatLng(sw2.lat, sw2.lng);
              this._northEast = new LatLng(ne2.lat, ne2.lng);
            } else {
              sw.lat = Math.min(sw2.lat, sw.lat);
              sw.lng = Math.min(sw2.lng, sw.lng);
              ne.lat = Math.max(ne2.lat, ne.lat);
              ne.lng = Math.max(ne2.lng, ne.lng);
            }
            return this;
          },
          // @method pad(bufferRatio: Number): LatLngBounds
          // Returns bounds created by extending or retracting the current bounds by a given ratio in each direction.
          // For example, a ratio of 0.5 extends the bounds by 50% in each direction.
          // Negative values will retract the bounds.
          pad: function(bufferRatio) {
            var sw = this._southWest, ne = this._northEast, heightBuffer = Math.abs(sw.lat - ne.lat) * bufferRatio, widthBuffer = Math.abs(sw.lng - ne.lng) * bufferRatio;
            return new LatLngBounds(
              new LatLng(sw.lat - heightBuffer, sw.lng - widthBuffer),
              new LatLng(ne.lat + heightBuffer, ne.lng + widthBuffer)
            );
          },
          // @method getCenter(): LatLng
          // Returns the center point of the bounds.
          getCenter: function() {
            return new LatLng(
              (this._southWest.lat + this._northEast.lat) / 2,
              (this._southWest.lng + this._northEast.lng) / 2
            );
          },
          // @method getSouthWest(): LatLng
          // Returns the south-west point of the bounds.
          getSouthWest: function() {
            return this._southWest;
          },
          // @method getNorthEast(): LatLng
          // Returns the north-east point of the bounds.
          getNorthEast: function() {
            return this._northEast;
          },
          // @method getNorthWest(): LatLng
          // Returns the north-west point of the bounds.
          getNorthWest: function() {
            return new LatLng(this.getNorth(), this.getWest());
          },
          // @method getSouthEast(): LatLng
          // Returns the south-east point of the bounds.
          getSouthEast: function() {
            return new LatLng(this.getSouth(), this.getEast());
          },
          // @method getWest(): Number
          // Returns the west longitude of the bounds
          getWest: function() {
            return this._southWest.lng;
          },
          // @method getSouth(): Number
          // Returns the south latitude of the bounds
          getSouth: function() {
            return this._southWest.lat;
          },
          // @method getEast(): Number
          // Returns the east longitude of the bounds
          getEast: function() {
            return this._northEast.lng;
          },
          // @method getNorth(): Number
          // Returns the north latitude of the bounds
          getNorth: function() {
            return this._northEast.lat;
          },
          // @method contains(otherBounds: LatLngBounds): Boolean
          // Returns `true` if the rectangle contains the given one.
          // @alternative
          // @method contains (latlng: LatLng): Boolean
          // Returns `true` if the rectangle contains the given point.
          contains: function(obj) {
            if (typeof obj[0] === "number" || obj instanceof LatLng || "lat" in obj) {
              obj = toLatLng(obj);
            } else {
              obj = toLatLngBounds(obj);
            }
            var sw = this._southWest, ne = this._northEast, sw2, ne2;
            if (obj instanceof LatLngBounds) {
              sw2 = obj.getSouthWest();
              ne2 = obj.getNorthEast();
            } else {
              sw2 = ne2 = obj;
            }
            return sw2.lat >= sw.lat && ne2.lat <= ne.lat && sw2.lng >= sw.lng && ne2.lng <= ne.lng;
          },
          // @method intersects(otherBounds: LatLngBounds): Boolean
          // Returns `true` if the rectangle intersects the given bounds. Two bounds intersect if they have at least one point in common.
          intersects: function(bounds) {
            bounds = toLatLngBounds(bounds);
            var sw = this._southWest, ne = this._northEast, sw2 = bounds.getSouthWest(), ne2 = bounds.getNorthEast(), latIntersects = ne2.lat >= sw.lat && sw2.lat <= ne.lat, lngIntersects = ne2.lng >= sw.lng && sw2.lng <= ne.lng;
            return latIntersects && lngIntersects;
          },
          // @method overlaps(otherBounds: LatLngBounds): Boolean
          // Returns `true` if the rectangle overlaps the given bounds. Two bounds overlap if their intersection is an area.
          overlaps: function(bounds) {
            bounds = toLatLngBounds(bounds);
            var sw = this._southWest, ne = this._northEast, sw2 = bounds.getSouthWest(), ne2 = bounds.getNorthEast(), latOverlaps = ne2.lat > sw.lat && sw2.lat < ne.lat, lngOverlaps = ne2.lng > sw.lng && sw2.lng < ne.lng;
            return latOverlaps && lngOverlaps;
          },
          // @method toBBoxString(): String
          // Returns a string with bounding box coordinates in a 'southwest_lng,southwest_lat,northeast_lng,northeast_lat' format. Useful for sending requests to web services that return geo data.
          toBBoxString: function() {
            return [this.getWest(), this.getSouth(), this.getEast(), this.getNorth()].join(",");
          },
          // @method equals(otherBounds: LatLngBounds, maxMargin?: Number): Boolean
          // Returns `true` if the rectangle is equivalent (within a small margin of error) to the given bounds. The margin of error can be overridden by setting `maxMargin` to a small number.
          equals: function(bounds, maxMargin) {
            if (!bounds) {
              return false;
            }
            bounds = toLatLngBounds(bounds);
            return this._southWest.equals(bounds.getSouthWest(), maxMargin) && this._northEast.equals(bounds.getNorthEast(), maxMargin);
          },
          // @method isValid(): Boolean
          // Returns `true` if the bounds are properly initialized.
          isValid: function() {
            return !!(this._southWest && this._northEast);
          }
        };
        function toLatLngBounds(a, b) {
          if (a instanceof LatLngBounds) {
            return a;
          }
          return new LatLngBounds(a, b);
        }
        function LatLng(lat, lng, alt) {
          if (isNaN(lat) || isNaN(lng)) {
            throw new Error("Invalid LatLng object: (" + lat + ", " + lng + ")");
          }
          this.lat = +lat;
          this.lng = +lng;
          if (alt !== void 0) {
            this.alt = +alt;
          }
        }
        LatLng.prototype = {
          // @method equals(otherLatLng: LatLng, maxMargin?: Number): Boolean
          // Returns `true` if the given `LatLng` point is at the same position (within a small margin of error). The margin of error can be overridden by setting `maxMargin` to a small number.
          equals: function(obj, maxMargin) {
            if (!obj) {
              return false;
            }
            obj = toLatLng(obj);
            var margin = Math.max(
              Math.abs(this.lat - obj.lat),
              Math.abs(this.lng - obj.lng)
            );
            return margin <= (maxMargin === void 0 ? 1e-9 : maxMargin);
          },
          // @method toString(): String
          // Returns a string representation of the point (for debugging purposes).
          toString: function(precision) {
            return "LatLng(" + formatNum(this.lat, precision) + ", " + formatNum(this.lng, precision) + ")";
          },
          // @method distanceTo(otherLatLng: LatLng): Number
          // Returns the distance (in meters) to the given `LatLng` calculated using the [Spherical Law of Cosines](https://en.wikipedia.org/wiki/Spherical_law_of_cosines).
          distanceTo: function(other) {
            return Earth.distance(this, toLatLng(other));
          },
          // @method wrap(): LatLng
          // Returns a new `LatLng` object with the longitude wrapped so it's always between -180 and +180 degrees.
          wrap: function() {
            return Earth.wrapLatLng(this);
          },
          // @method toBounds(sizeInMeters: Number): LatLngBounds
          // Returns a new `LatLngBounds` object in which each boundary is `sizeInMeters/2` meters apart from the `LatLng`.
          toBounds: function(sizeInMeters) {
            var latAccuracy = 180 * sizeInMeters / 40075017, lngAccuracy = latAccuracy / Math.cos(Math.PI / 180 * this.lat);
            return toLatLngBounds(
              [this.lat - latAccuracy, this.lng - lngAccuracy],
              [this.lat + latAccuracy, this.lng + lngAccuracy]
            );
          },
          clone: function() {
            return new LatLng(this.lat, this.lng, this.alt);
          }
        };
        function toLatLng(a, b, c) {
          if (a instanceof LatLng) {
            return a;
          }
          if (isArray(a) && typeof a[0] !== "object") {
            if (a.length === 3) {
              return new LatLng(a[0], a[1], a[2]);
            }
            if (a.length === 2) {
              return new LatLng(a[0], a[1]);
            }
            return null;
          }
          if (a === void 0 || a === null) {
            return a;
          }
          if (typeof a === "object" && "lat" in a) {
            return new LatLng(a.lat, "lng" in a ? a.lng : a.lon, a.alt);
          }
          if (b === void 0) {
            return null;
          }
          return new LatLng(a, b, c);
        }
        var CRS = {
          // @method latLngToPoint(latlng: LatLng, zoom: Number): Point
          // Projects geographical coordinates into pixel coordinates for a given zoom.
          latLngToPoint: function(latlng, zoom2) {
            var projectedPoint = this.projection.project(latlng), scale2 = this.scale(zoom2);
            return this.transformation._transform(projectedPoint, scale2);
          },
          // @method pointToLatLng(point: Point, zoom: Number): LatLng
          // The inverse of `latLngToPoint`. Projects pixel coordinates on a given
          // zoom into geographical coordinates.
          pointToLatLng: function(point, zoom2) {
            var scale2 = this.scale(zoom2), untransformedPoint = this.transformation.untransform(point, scale2);
            return this.projection.unproject(untransformedPoint);
          },
          // @method project(latlng: LatLng): Point
          // Projects geographical coordinates into coordinates in units accepted for
          // this CRS (e.g. meters for EPSG:3857, for passing it to WMS services).
          project: function(latlng) {
            return this.projection.project(latlng);
          },
          // @method unproject(point: Point): LatLng
          // Given a projected coordinate returns the corresponding LatLng.
          // The inverse of `project`.
          unproject: function(point) {
            return this.projection.unproject(point);
          },
          // @method scale(zoom: Number): Number
          // Returns the scale used when transforming projected coordinates into
          // pixel coordinates for a particular zoom. For example, it returns
          // `256 * 2^zoom` for Mercator-based CRS.
          scale: function(zoom2) {
            return 256 * Math.pow(2, zoom2);
          },
          // @method zoom(scale: Number): Number
          // Inverse of `scale()`, returns the zoom level corresponding to a scale
          // factor of `scale`.
          zoom: function(scale2) {
            return Math.log(scale2 / 256) / Math.LN2;
          },
          // @method getProjectedBounds(zoom: Number): Bounds
          // Returns the projection's bounds scaled and transformed for the provided `zoom`.
          getProjectedBounds: function(zoom2) {
            if (this.infinite) {
              return null;
            }
            var b = this.projection.bounds, s = this.scale(zoom2), min = this.transformation.transform(b.min, s), max = this.transformation.transform(b.max, s);
            return new Bounds(min, max);
          },
          // @method distance(latlng1: LatLng, latlng2: LatLng): Number
          // Returns the distance between two geographical coordinates.
          // @property code: String
          // Standard code name of the CRS passed into WMS services (e.g. `'EPSG:3857'`)
          //
          // @property wrapLng: Number[]
          // An array of two numbers defining whether the longitude (horizontal) coordinate
          // axis wraps around a given range and how. Defaults to `[-180, 180]` in most
          // geographical CRSs. If `undefined`, the longitude axis does not wrap around.
          //
          // @property wrapLat: Number[]
          // Like `wrapLng`, but for the latitude (vertical) axis.
          // wrapLng: [min, max],
          // wrapLat: [min, max],
          // @property infinite: Boolean
          // If true, the coordinate space will be unbounded (infinite in both axes)
          infinite: false,
          // @method wrapLatLng(latlng: LatLng): LatLng
          // Returns a `LatLng` where lat and lng has been wrapped according to the
          // CRS's `wrapLat` and `wrapLng` properties, if they are outside the CRS's bounds.
          wrapLatLng: function(latlng) {
            var lng = this.wrapLng ? wrapNum(latlng.lng, this.wrapLng, true) : latlng.lng, lat = this.wrapLat ? wrapNum(latlng.lat, this.wrapLat, true) : latlng.lat, alt = latlng.alt;
            return new LatLng(lat, lng, alt);
          },
          // @method wrapLatLngBounds(bounds: LatLngBounds): LatLngBounds
          // Returns a `LatLngBounds` with the same size as the given one, ensuring
          // that its center is within the CRS's bounds.
          // Only accepts actual `L.LatLngBounds` instances, not arrays.
          wrapLatLngBounds: function(bounds) {
            var center = bounds.getCenter(), newCenter = this.wrapLatLng(center), latShift = center.lat - newCenter.lat, lngShift = center.lng - newCenter.lng;
            if (latShift === 0 && lngShift === 0) {
              return bounds;
            }
            var sw = bounds.getSouthWest(), ne = bounds.getNorthEast(), newSw = new LatLng(sw.lat - latShift, sw.lng - lngShift), newNe = new LatLng(ne.lat - latShift, ne.lng - lngShift);
            return new LatLngBounds(newSw, newNe);
          }
        };
        var Earth = extend({}, CRS, {
          wrapLng: [-180, 180],
          // Mean Earth Radius, as recommended for use by
          // the International Union of Geodesy and Geophysics,
          // see https://rosettacode.org/wiki/Haversine_formula
          R: 6371e3,
          // distance between two geographical points using spherical law of cosines approximation
          distance: function(latlng1, latlng2) {
            var rad = Math.PI / 180, lat1 = latlng1.lat * rad, lat2 = latlng2.lat * rad, sinDLat = Math.sin((latlng2.lat - latlng1.lat) * rad / 2), sinDLon = Math.sin((latlng2.lng - latlng1.lng) * rad / 2), a = sinDLat * sinDLat + Math.cos(lat1) * Math.cos(lat2) * sinDLon * sinDLon, c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            return this.R * c;
          }
        });
        var earthRadius = 6378137;
        var SphericalMercator = {
          R: earthRadius,
          MAX_LATITUDE: 85.0511287798,
          project: function(latlng) {
            var d = Math.PI / 180, max = this.MAX_LATITUDE, lat = Math.max(Math.min(max, latlng.lat), -max), sin = Math.sin(lat * d);
            return new Point(
              this.R * latlng.lng * d,
              this.R * Math.log((1 + sin) / (1 - sin)) / 2
            );
          },
          unproject: function(point) {
            var d = 180 / Math.PI;
            return new LatLng(
              (2 * Math.atan(Math.exp(point.y / this.R)) - Math.PI / 2) * d,
              point.x * d / this.R
            );
          },
          bounds: function() {
            var d = earthRadius * Math.PI;
            return new Bounds([-d, -d], [d, d]);
          }()
        };
        function Transformation(a, b, c, d) {
          if (isArray(a)) {
            this._a = a[0];
            this._b = a[1];
            this._c = a[2];
            this._d = a[3];
            return;
          }
          this._a = a;
          this._b = b;
          this._c = c;
          this._d = d;
        }
        Transformation.prototype = {
          // @method transform(point: Point, scale?: Number): Point
          // Returns a transformed point, optionally multiplied by the given scale.
          // Only accepts actual `L.Point` instances, not arrays.
          transform: function(point, scale2) {
            return this._transform(point.clone(), scale2);
          },
          // destructive transform (faster)
          _transform: function(point, scale2) {
            scale2 = scale2 || 1;
            point.x = scale2 * (this._a * point.x + this._b);
            point.y = scale2 * (this._c * point.y + this._d);
            return point;
          },
          // @method untransform(point: Point, scale?: Number): Point
          // Returns the reverse transformation of the given point, optionally divided
          // by the given scale. Only accepts actual `L.Point` instances, not arrays.
          untransform: function(point, scale2) {
            scale2 = scale2 || 1;
            return new Point(
              (point.x / scale2 - this._b) / this._a,
              (point.y / scale2 - this._d) / this._c
            );
          }
        };
        function toTransformation(a, b, c, d) {
          return new Transformation(a, b, c, d);
        }
        var EPSG3857 = extend({}, Earth, {
          code: "EPSG:3857",
          projection: SphericalMercator,
          transformation: function() {
            var scale2 = 0.5 / (Math.PI * SphericalMercator.R);
            return toTransformation(scale2, 0.5, -scale2, 0.5);
          }()
        });
        var EPSG900913 = extend({}, EPSG3857, {
          code: "EPSG:900913"
        });
        function svgCreate(name) {
          return document.createElementNS("http://www.w3.org/2000/svg", name);
        }
        function pointsToPath(rings, closed) {
          var str = "", i, j, len, len2, points, p;
          for (i = 0, len = rings.length; i < len; i++) {
            points = rings[i];
            for (j = 0, len2 = points.length; j < len2; j++) {
              p = points[j];
              str += (j ? "L" : "M") + p.x + " " + p.y;
            }
            str += closed ? Browser.svg ? "z" : "x" : "";
          }
          return str || "M0 0";
        }
        var style = document.documentElement.style;
        var ie = "ActiveXObject" in window;
        var ielt9 = ie && !document.addEventListener;
        var edge = "msLaunchUri" in navigator && !("documentMode" in document);
        var webkit = userAgentContains("webkit");
        var android = userAgentContains("android");
        var android23 = userAgentContains("android 2") || userAgentContains("android 3");
        var webkitVer = parseInt(/WebKit\/([0-9]+)|$/.exec(navigator.userAgent)[1], 10);
        var androidStock = android && userAgentContains("Google") && webkitVer < 537 && !("AudioNode" in window);
        var opera = !!window.opera;
        var chrome = !edge && userAgentContains("chrome");
        var gecko = userAgentContains("gecko") && !webkit && !opera && !ie;
        var safari = !chrome && userAgentContains("safari");
        var phantom = userAgentContains("phantom");
        var opera12 = "OTransition" in style;
        var win = navigator.platform.indexOf("Win") === 0;
        var ie3d = ie && "transition" in style;
        var webkit3d = "WebKitCSSMatrix" in window && "m11" in new window.WebKitCSSMatrix() && !android23;
        var gecko3d = "MozPerspective" in style;
        var any3d = !window.L_DISABLE_3D && (ie3d || webkit3d || gecko3d) && !opera12 && !phantom;
        var mobile = typeof orientation !== "undefined" || userAgentContains("mobile");
        var mobileWebkit = mobile && webkit;
        var mobileWebkit3d = mobile && webkit3d;
        var msPointer = !window.PointerEvent && window.MSPointerEvent;
        var pointer = !!(window.PointerEvent || msPointer);
        var touchNative = "ontouchstart" in window || !!window.TouchEvent;
        var touch = !window.L_NO_TOUCH && (touchNative || pointer);
        var mobileOpera = mobile && opera;
        var mobileGecko = mobile && gecko;
        var retina = (window.devicePixelRatio || window.screen.deviceXDPI / window.screen.logicalXDPI) > 1;
        var passiveEvents = function() {
          var supportsPassiveOption = false;
          try {
            var opts = Object.defineProperty({}, "passive", {
              get: function() {
                supportsPassiveOption = true;
              }
            });
            window.addEventListener("testPassiveEventSupport", falseFn, opts);
            window.removeEventListener("testPassiveEventSupport", falseFn, opts);
          } catch (e) {
          }
          return supportsPassiveOption;
        }();
        var canvas$1 = function() {
          return !!document.createElement("canvas").getContext;
        }();
        var svg$1 = !!(document.createElementNS && svgCreate("svg").createSVGRect);
        var inlineSvg = !!svg$1 && function() {
          var div = document.createElement("div");
          div.innerHTML = "<svg/>";
          return (div.firstChild && div.firstChild.namespaceURI) === "http://www.w3.org/2000/svg";
        }();
        var vml = !svg$1 && function() {
          try {
            var div = document.createElement("div");
            div.innerHTML = '<v:shape adj="1"/>';
            var shape = div.firstChild;
            shape.style.behavior = "url(#default#VML)";
            return shape && typeof shape.adj === "object";
          } catch (e) {
            return false;
          }
        }();
        var mac = navigator.platform.indexOf("Mac") === 0;
        var linux = navigator.platform.indexOf("Linux") === 0;
        function userAgentContains(str) {
          return navigator.userAgent.toLowerCase().indexOf(str) >= 0;
        }
        var Browser = {
          ie,
          ielt9,
          edge,
          webkit,
          android,
          android23,
          androidStock,
          opera,
          chrome,
          gecko,
          safari,
          phantom,
          opera12,
          win,
          ie3d,
          webkit3d,
          gecko3d,
          any3d,
          mobile,
          mobileWebkit,
          mobileWebkit3d,
          msPointer,
          pointer,
          touch,
          touchNative,
          mobileOpera,
          mobileGecko,
          retina,
          passiveEvents,
          canvas: canvas$1,
          svg: svg$1,
          vml,
          inlineSvg,
          mac,
          linux
        };
        var POINTER_DOWN = Browser.msPointer ? "MSPointerDown" : "pointerdown";
        var POINTER_MOVE = Browser.msPointer ? "MSPointerMove" : "pointermove";
        var POINTER_UP = Browser.msPointer ? "MSPointerUp" : "pointerup";
        var POINTER_CANCEL = Browser.msPointer ? "MSPointerCancel" : "pointercancel";
        var pEvent = {
          touchstart: POINTER_DOWN,
          touchmove: POINTER_MOVE,
          touchend: POINTER_UP,
          touchcancel: POINTER_CANCEL
        };
        var handle = {
          touchstart: _onPointerStart,
          touchmove: _handlePointer,
          touchend: _handlePointer,
          touchcancel: _handlePointer
        };
        var _pointers = {};
        var _pointerDocListener = false;
        function addPointerListener(obj, type2, handler) {
          if (type2 === "touchstart") {
            _addPointerDocListener();
          }
          if (!handle[type2]) {
            console.warn("wrong event specified:", type2);
            return falseFn;
          }
          handler = handle[type2].bind(this, handler);
          obj.addEventListener(pEvent[type2], handler, false);
          return handler;
        }
        function removePointerListener(obj, type2, handler) {
          if (!pEvent[type2]) {
            console.warn("wrong event specified:", type2);
            return;
          }
          obj.removeEventListener(pEvent[type2], handler, false);
        }
        function _globalPointerDown(e) {
          _pointers[e.pointerId] = e;
        }
        function _globalPointerMove(e) {
          if (_pointers[e.pointerId]) {
            _pointers[e.pointerId] = e;
          }
        }
        function _globalPointerUp(e) {
          delete _pointers[e.pointerId];
        }
        function _addPointerDocListener() {
          if (!_pointerDocListener) {
            document.addEventListener(POINTER_DOWN, _globalPointerDown, true);
            document.addEventListener(POINTER_MOVE, _globalPointerMove, true);
            document.addEventListener(POINTER_UP, _globalPointerUp, true);
            document.addEventListener(POINTER_CANCEL, _globalPointerUp, true);
            _pointerDocListener = true;
          }
        }
        function _handlePointer(handler, e) {
          if (e.pointerType === (e.MSPOINTER_TYPE_MOUSE || "mouse")) {
            return;
          }
          e.touches = [];
          for (var i in _pointers) {
            e.touches.push(_pointers[i]);
          }
          e.changedTouches = [e];
          handler(e);
        }
        function _onPointerStart(handler, e) {
          if (e.MSPOINTER_TYPE_TOUCH && e.pointerType === e.MSPOINTER_TYPE_TOUCH) {
            preventDefault(e);
          }
          _handlePointer(handler, e);
        }
        function makeDblclick(event) {
          var newEvent = {}, prop, i;
          for (i in event) {
            prop = event[i];
            newEvent[i] = prop && prop.bind ? prop.bind(event) : prop;
          }
          event = newEvent;
          newEvent.type = "dblclick";
          newEvent.detail = 2;
          newEvent.isTrusted = false;
          newEvent._simulated = true;
          return newEvent;
        }
        var delay = 200;
        function addDoubleTapListener(obj, handler) {
          obj.addEventListener("dblclick", handler);
          var last = 0, detail;
          function simDblclick(e) {
            if (e.detail !== 1) {
              detail = e.detail;
              return;
            }
            if (e.pointerType === "mouse" || e.sourceCapabilities && !e.sourceCapabilities.firesTouchEvents) {
              return;
            }
            var path = getPropagationPath(e);
            if (path.some(function(el) {
              return el instanceof HTMLLabelElement && el.attributes.for;
            }) && !path.some(function(el) {
              return el instanceof HTMLInputElement || el instanceof HTMLSelectElement;
            })) {
              return;
            }
            var now = Date.now();
            if (now - last <= delay) {
              detail++;
              if (detail === 2) {
                handler(makeDblclick(e));
              }
            } else {
              detail = 1;
            }
            last = now;
          }
          obj.addEventListener("click", simDblclick);
          return {
            dblclick: handler,
            simDblclick
          };
        }
        function removeDoubleTapListener(obj, handlers) {
          obj.removeEventListener("dblclick", handlers.dblclick);
          obj.removeEventListener("click", handlers.simDblclick);
        }
        var TRANSFORM = testProp(
          ["transform", "webkitTransform", "OTransform", "MozTransform", "msTransform"]
        );
        var TRANSITION = testProp(
          ["webkitTransition", "transition", "OTransition", "MozTransition", "msTransition"]
        );
        var TRANSITION_END = TRANSITION === "webkitTransition" || TRANSITION === "OTransition" ? TRANSITION + "End" : "transitionend";
        function get(id) {
          return typeof id === "string" ? document.getElementById(id) : id;
        }
        function getStyle(el, style2) {
          var value = el.style[style2] || el.currentStyle && el.currentStyle[style2];
          if ((!value || value === "auto") && document.defaultView) {
            var css = document.defaultView.getComputedStyle(el, null);
            value = css ? css[style2] : null;
          }
          return value === "auto" ? null : value;
        }
        function create$1(tagName, className, container) {
          var el = document.createElement(tagName);
          el.className = className || "";
          if (container) {
            container.appendChild(el);
          }
          return el;
        }
        function remove(el) {
          var parent = el.parentNode;
          if (parent) {
            parent.removeChild(el);
          }
        }
        function empty(el) {
          while (el.firstChild) {
            el.removeChild(el.firstChild);
          }
        }
        function toFront(el) {
          var parent = el.parentNode;
          if (parent && parent.lastChild !== el) {
            parent.appendChild(el);
          }
        }
        function toBack(el) {
          var parent = el.parentNode;
          if (parent && parent.firstChild !== el) {
            parent.insertBefore(el, parent.firstChild);
          }
        }
        function hasClass(el, name) {
          if (el.classList !== void 0) {
            return el.classList.contains(name);
          }
          var className = getClass(el);
          return className.length > 0 && new RegExp("(^|\\s)" + name + "(\\s|$)").test(className);
        }
        function addClass(el, name) {
          if (el.classList !== void 0) {
            var classes = splitWords(name);
            for (var i = 0, len = classes.length; i < len; i++) {
              el.classList.add(classes[i]);
            }
          } else if (!hasClass(el, name)) {
            var className = getClass(el);
            setClass(el, (className ? className + " " : "") + name);
          }
        }
        function removeClass(el, name) {
          if (el.classList !== void 0) {
            el.classList.remove(name);
          } else {
            setClass(el, trim((" " + getClass(el) + " ").replace(" " + name + " ", " ")));
          }
        }
        function setClass(el, name) {
          if (el.className.baseVal === void 0) {
            el.className = name;
          } else {
            el.className.baseVal = name;
          }
        }
        function getClass(el) {
          if (el.correspondingElement) {
            el = el.correspondingElement;
          }
          return el.className.baseVal === void 0 ? el.className : el.className.baseVal;
        }
        function setOpacity(el, value) {
          if ("opacity" in el.style) {
            el.style.opacity = value;
          } else if ("filter" in el.style) {
            _setOpacityIE(el, value);
          }
        }
        function _setOpacityIE(el, value) {
          var filter = false, filterName = "DXImageTransform.Microsoft.Alpha";
          try {
            filter = el.filters.item(filterName);
          } catch (e) {
            if (value === 1) {
              return;
            }
          }
          value = Math.round(value * 100);
          if (filter) {
            filter.Enabled = value !== 100;
            filter.Opacity = value;
          } else {
            el.style.filter += " progid:" + filterName + "(opacity=" + value + ")";
          }
        }
        function testProp(props) {
          var style2 = document.documentElement.style;
          for (var i = 0; i < props.length; i++) {
            if (props[i] in style2) {
              return props[i];
            }
          }
          return false;
        }
        function setTransform(el, offset, scale2) {
          var pos = offset || new Point(0, 0);
          el.style[TRANSFORM] = (Browser.ie3d ? "translate(" + pos.x + "px," + pos.y + "px)" : "translate3d(" + pos.x + "px," + pos.y + "px,0)") + (scale2 ? " scale(" + scale2 + ")" : "");
        }
        function setPosition(el, point) {
          el._leaflet_pos = point;
          if (Browser.any3d) {
            setTransform(el, point);
          } else {
            el.style.left = point.x + "px";
            el.style.top = point.y + "px";
          }
        }
        function getPosition(el) {
          return el._leaflet_pos || new Point(0, 0);
        }
        var disableTextSelection;
        var enableTextSelection;
        var _userSelect;
        if ("onselectstart" in document) {
          disableTextSelection = function() {
            on(window, "selectstart", preventDefault);
          };
          enableTextSelection = function() {
            off(window, "selectstart", preventDefault);
          };
        } else {
          var userSelectProperty = testProp(
            ["userSelect", "WebkitUserSelect", "OUserSelect", "MozUserSelect", "msUserSelect"]
          );
          disableTextSelection = function() {
            if (userSelectProperty) {
              var style2 = document.documentElement.style;
              _userSelect = style2[userSelectProperty];
              style2[userSelectProperty] = "none";
            }
          };
          enableTextSelection = function() {
            if (userSelectProperty) {
              document.documentElement.style[userSelectProperty] = _userSelect;
              _userSelect = void 0;
            }
          };
        }
        function disableImageDrag() {
          on(window, "dragstart", preventDefault);
        }
        function enableImageDrag() {
          off(window, "dragstart", preventDefault);
        }
        var _outlineElement, _outlineStyle;
        function preventOutline(element) {
          while (element.tabIndex === -1) {
            element = element.parentNode;
          }
          if (!element.style) {
            return;
          }
          restoreOutline();
          _outlineElement = element;
          _outlineStyle = element.style.outlineStyle;
          element.style.outlineStyle = "none";
          on(window, "keydown", restoreOutline);
        }
        function restoreOutline() {
          if (!_outlineElement) {
            return;
          }
          _outlineElement.style.outlineStyle = _outlineStyle;
          _outlineElement = void 0;
          _outlineStyle = void 0;
          off(window, "keydown", restoreOutline);
        }
        function getSizedParentNode(element) {
          do {
            element = element.parentNode;
          } while ((!element.offsetWidth || !element.offsetHeight) && element !== document.body);
          return element;
        }
        function getScale(element) {
          var rect = element.getBoundingClientRect();
          return {
            x: rect.width / element.offsetWidth || 1,
            y: rect.height / element.offsetHeight || 1,
            boundingClientRect: rect
          };
        }
        var DomUtil = {
          __proto__: null,
          TRANSFORM,
          TRANSITION,
          TRANSITION_END,
          get,
          getStyle,
          create: create$1,
          remove,
          empty,
          toFront,
          toBack,
          hasClass,
          addClass,
          removeClass,
          setClass,
          getClass,
          setOpacity,
          testProp,
          setTransform,
          setPosition,
          getPosition,
          get disableTextSelection() {
            return disableTextSelection;
          },
          get enableTextSelection() {
            return enableTextSelection;
          },
          disableImageDrag,
          enableImageDrag,
          preventOutline,
          restoreOutline,
          getSizedParentNode,
          getScale
        };
        function on(obj, types, fn, context) {
          if (types && typeof types === "object") {
            for (var type2 in types) {
              addOne(obj, type2, types[type2], fn);
            }
          } else {
            types = splitWords(types);
            for (var i = 0, len = types.length; i < len; i++) {
              addOne(obj, types[i], fn, context);
            }
          }
          return this;
        }
        var eventsKey = "_leaflet_events";
        function off(obj, types, fn, context) {
          if (arguments.length === 1) {
            batchRemove(obj);
            delete obj[eventsKey];
          } else if (types && typeof types === "object") {
            for (var type2 in types) {
              removeOne(obj, type2, types[type2], fn);
            }
          } else {
            types = splitWords(types);
            if (arguments.length === 2) {
              batchRemove(obj, function(type3) {
                return indexOf(types, type3) !== -1;
              });
            } else {
              for (var i = 0, len = types.length; i < len; i++) {
                removeOne(obj, types[i], fn, context);
              }
            }
          }
          return this;
        }
        function batchRemove(obj, filterFn) {
          for (var id in obj[eventsKey]) {
            var type2 = id.split(/\d/)[0];
            if (!filterFn || filterFn(type2)) {
              removeOne(obj, type2, null, null, id);
            }
          }
        }
        var mouseSubst = {
          mouseenter: "mouseover",
          mouseleave: "mouseout",
          wheel: !("onwheel" in window) && "mousewheel"
        };
        function addOne(obj, type2, fn, context) {
          var id = type2 + stamp(fn) + (context ? "_" + stamp(context) : "");
          if (obj[eventsKey] && obj[eventsKey][id]) {
            return this;
          }
          var handler = function(e) {
            return fn.call(context || obj, e || window.event);
          };
          var originalHandler = handler;
          if (!Browser.touchNative && Browser.pointer && type2.indexOf("touch") === 0) {
            handler = addPointerListener(obj, type2, handler);
          } else if (Browser.touch && type2 === "dblclick") {
            handler = addDoubleTapListener(obj, handler);
          } else if ("addEventListener" in obj) {
            if (type2 === "touchstart" || type2 === "touchmove" || type2 === "wheel" || type2 === "mousewheel") {
              obj.addEventListener(mouseSubst[type2] || type2, handler, Browser.passiveEvents ? { passive: false } : false);
            } else if (type2 === "mouseenter" || type2 === "mouseleave") {
              handler = function(e) {
                e = e || window.event;
                if (isExternalTarget(obj, e)) {
                  originalHandler(e);
                }
              };
              obj.addEventListener(mouseSubst[type2], handler, false);
            } else {
              obj.addEventListener(type2, originalHandler, false);
            }
          } else {
            obj.attachEvent("on" + type2, handler);
          }
          obj[eventsKey] = obj[eventsKey] || {};
          obj[eventsKey][id] = handler;
        }
        function removeOne(obj, type2, fn, context, id) {
          id = id || type2 + stamp(fn) + (context ? "_" + stamp(context) : "");
          var handler = obj[eventsKey] && obj[eventsKey][id];
          if (!handler) {
            return this;
          }
          if (!Browser.touchNative && Browser.pointer && type2.indexOf("touch") === 0) {
            removePointerListener(obj, type2, handler);
          } else if (Browser.touch && type2 === "dblclick") {
            removeDoubleTapListener(obj, handler);
          } else if ("removeEventListener" in obj) {
            obj.removeEventListener(mouseSubst[type2] || type2, handler, false);
          } else {
            obj.detachEvent("on" + type2, handler);
          }
          obj[eventsKey][id] = null;
        }
        function stopPropagation(e) {
          if (e.stopPropagation) {
            e.stopPropagation();
          } else if (e.originalEvent) {
            e.originalEvent._stopped = true;
          } else {
            e.cancelBubble = true;
          }
          return this;
        }
        function disableScrollPropagation(el) {
          addOne(el, "wheel", stopPropagation);
          return this;
        }
        function disableClickPropagation(el) {
          on(el, "mousedown touchstart dblclick contextmenu", stopPropagation);
          el["_leaflet_disable_click"] = true;
          return this;
        }
        function preventDefault(e) {
          if (e.preventDefault) {
            e.preventDefault();
          } else {
            e.returnValue = false;
          }
          return this;
        }
        function stop(e) {
          preventDefault(e);
          stopPropagation(e);
          return this;
        }
        function getPropagationPath(ev) {
          if (ev.composedPath) {
            return ev.composedPath();
          }
          var path = [];
          var el = ev.target;
          while (el) {
            path.push(el);
            el = el.parentNode;
          }
          return path;
        }
        function getMousePosition(e, container) {
          if (!container) {
            return new Point(e.clientX, e.clientY);
          }
          var scale2 = getScale(container), offset = scale2.boundingClientRect;
          return new Point(
            // offset.left/top values are in page scale (like clientX/Y),
            // whereas clientLeft/Top (border width) values are the original values (before CSS scale applies).
            (e.clientX - offset.left) / scale2.x - container.clientLeft,
            (e.clientY - offset.top) / scale2.y - container.clientTop
          );
        }
        var wheelPxFactor = Browser.linux && Browser.chrome ? window.devicePixelRatio : Browser.mac ? window.devicePixelRatio * 3 : window.devicePixelRatio > 0 ? 2 * window.devicePixelRatio : 1;
        function getWheelDelta(e) {
          return Browser.edge ? e.wheelDeltaY / 2 : (
            // Don't trust window-geometry-based delta
            e.deltaY && e.deltaMode === 0 ? -e.deltaY / wheelPxFactor : (
              // Pixels
              e.deltaY && e.deltaMode === 1 ? -e.deltaY * 20 : (
                // Lines
                e.deltaY && e.deltaMode === 2 ? -e.deltaY * 60 : (
                  // Pages
                  e.deltaX || e.deltaZ ? 0 : (
                    // Skip horizontal/depth wheel events
                    e.wheelDelta ? (e.wheelDeltaY || e.wheelDelta) / 2 : (
                      // Legacy IE pixels
                      e.detail && Math.abs(e.detail) < 32765 ? -e.detail * 20 : (
                        // Legacy Moz lines
                        e.detail ? e.detail / -32765 * 60 : (
                          // Legacy Moz pages
                          0
                        )
                      )
                    )
                  )
                )
              )
            )
          );
        }
        function isExternalTarget(el, e) {
          var related = e.relatedTarget;
          if (!related) {
            return true;
          }
          try {
            while (related && related !== el) {
              related = related.parentNode;
            }
          } catch (err) {
            return false;
          }
          return related !== el;
        }
        var DomEvent = {
          __proto__: null,
          on,
          off,
          stopPropagation,
          disableScrollPropagation,
          disableClickPropagation,
          preventDefault,
          stop,
          getPropagationPath,
          getMousePosition,
          getWheelDelta,
          isExternalTarget,
          addListener: on,
          removeListener: off
        };
        var PosAnimation = Evented.extend({
          // @method run(el: HTMLElement, newPos: Point, duration?: Number, easeLinearity?: Number)
          // Run an animation of a given element to a new position, optionally setting
          // duration in seconds (`0.25` by default) and easing linearity factor (3rd
          // argument of the [cubic bezier curve](https://cubic-bezier.com/#0,0,.5,1),
          // `0.5` by default).
          run: function(el, newPos, duration, easeLinearity) {
            this.stop();
            this._el = el;
            this._inProgress = true;
            this._duration = duration || 0.25;
            this._easeOutPower = 1 / Math.max(easeLinearity || 0.5, 0.2);
            this._startPos = getPosition(el);
            this._offset = newPos.subtract(this._startPos);
            this._startTime = +/* @__PURE__ */ new Date();
            this.fire("start");
            this._animate();
          },
          // @method stop()
          // Stops the animation (if currently running).
          stop: function() {
            if (!this._inProgress) {
              return;
            }
            this._step(true);
            this._complete();
          },
          _animate: function() {
            this._animId = requestAnimFrame(this._animate, this);
            this._step();
          },
          _step: function(round) {
            var elapsed = +/* @__PURE__ */ new Date() - this._startTime, duration = this._duration * 1e3;
            if (elapsed < duration) {
              this._runFrame(this._easeOut(elapsed / duration), round);
            } else {
              this._runFrame(1);
              this._complete();
            }
          },
          _runFrame: function(progress, round) {
            var pos = this._startPos.add(this._offset.multiplyBy(progress));
            if (round) {
              pos._round();
            }
            setPosition(this._el, pos);
            this.fire("step");
          },
          _complete: function() {
            cancelAnimFrame(this._animId);
            this._inProgress = false;
            this.fire("end");
          },
          _easeOut: function(t) {
            return 1 - Math.pow(1 - t, this._easeOutPower);
          }
        });
        var Map3 = Evented.extend({
          options: {
            // @section Map State Options
            // @option crs: CRS = L.CRS.EPSG3857
            // The [Coordinate Reference System](#crs) to use. Don't change this if you're not
            // sure what it means.
            crs: EPSG3857,
            // @option center: LatLng = undefined
            // Initial geographic center of the map
            center: void 0,
            // @option zoom: Number = undefined
            // Initial map zoom level
            zoom: void 0,
            // @option minZoom: Number = *
            // Minimum zoom level of the map.
            // If not specified and at least one `GridLayer` or `TileLayer` is in the map,
            // the lowest of their `minZoom` options will be used instead.
            minZoom: void 0,
            // @option maxZoom: Number = *
            // Maximum zoom level of the map.
            // If not specified and at least one `GridLayer` or `TileLayer` is in the map,
            // the highest of their `maxZoom` options will be used instead.
            maxZoom: void 0,
            // @option layers: Layer[] = []
            // Array of layers that will be added to the map initially
            layers: [],
            // @option maxBounds: LatLngBounds = null
            // When this option is set, the map restricts the view to the given
            // geographical bounds, bouncing the user back if the user tries to pan
            // outside the view. To set the restriction dynamically, use
            // [`setMaxBounds`](#map-setmaxbounds) method.
            maxBounds: void 0,
            // @option renderer: Renderer = *
            // The default method for drawing vector layers on the map. `L.SVG`
            // or `L.Canvas` by default depending on browser support.
            renderer: void 0,
            // @section Animation Options
            // @option zoomAnimation: Boolean = true
            // Whether the map zoom animation is enabled. By default it's enabled
            // in all browsers that support CSS3 Transitions except Android.
            zoomAnimation: true,
            // @option zoomAnimationThreshold: Number = 4
            // Won't animate zoom if the zoom difference exceeds this value.
            zoomAnimationThreshold: 4,
            // @option fadeAnimation: Boolean = true
            // Whether the tile fade animation is enabled. By default it's enabled
            // in all browsers that support CSS3 Transitions except Android.
            fadeAnimation: true,
            // @option markerZoomAnimation: Boolean = true
            // Whether markers animate their zoom with the zoom animation, if disabled
            // they will disappear for the length of the animation. By default it's
            // enabled in all browsers that support CSS3 Transitions except Android.
            markerZoomAnimation: true,
            // @option transform3DLimit: Number = 2^23
            // Defines the maximum size of a CSS translation transform. The default
            // value should not be changed unless a web browser positions layers in
            // the wrong place after doing a large `panBy`.
            transform3DLimit: 8388608,
            // Precision limit of a 32-bit float
            // @section Interaction Options
            // @option zoomSnap: Number = 1
            // Forces the map's zoom level to always be a multiple of this, particularly
            // right after a [`fitBounds()`](#map-fitbounds) or a pinch-zoom.
            // By default, the zoom level snaps to the nearest integer; lower values
            // (e.g. `0.5` or `0.1`) allow for greater granularity. A value of `0`
            // means the zoom level will not be snapped after `fitBounds` or a pinch-zoom.
            zoomSnap: 1,
            // @option zoomDelta: Number = 1
            // Controls how much the map's zoom level will change after a
            // [`zoomIn()`](#map-zoomin), [`zoomOut()`](#map-zoomout), pressing `+`
            // or `-` on the keyboard, or using the [zoom controls](#control-zoom).
            // Values smaller than `1` (e.g. `0.5`) allow for greater granularity.
            zoomDelta: 1,
            // @option trackResize: Boolean = true
            // Whether the map automatically handles browser window resize to update itself.
            trackResize: true
          },
          initialize: function(id, options) {
            options = setOptions(this, options);
            this._handlers = [];
            this._layers = {};
            this._zoomBoundLayers = {};
            this._sizeChanged = true;
            this._initContainer(id);
            this._initLayout();
            this._onResize = bind(this._onResize, this);
            this._initEvents();
            if (options.maxBounds) {
              this.setMaxBounds(options.maxBounds);
            }
            if (options.zoom !== void 0) {
              this._zoom = this._limitZoom(options.zoom);
            }
            if (options.center && options.zoom !== void 0) {
              this.setView(toLatLng(options.center), options.zoom, { reset: true });
            }
            this.callInitHooks();
            this._zoomAnimated = TRANSITION && Browser.any3d && !Browser.mobileOpera && this.options.zoomAnimation;
            if (this._zoomAnimated) {
              this._createAnimProxy();
              on(this._proxy, TRANSITION_END, this._catchTransitionEnd, this);
            }
            this._addLayers(this.options.layers);
          },
          // @section Methods for modifying map state
          // @method setView(center: LatLng, zoom: Number, options?: Zoom/pan options): this
          // Sets the view of the map (geographical center and zoom) with the given
          // animation options.
          setView: function(center, zoom2, options) {
            zoom2 = zoom2 === void 0 ? this._zoom : this._limitZoom(zoom2);
            center = this._limitCenter(toLatLng(center), zoom2, this.options.maxBounds);
            options = options || {};
            this._stop();
            if (this._loaded && !options.reset && options !== true) {
              if (options.animate !== void 0) {
                options.zoom = extend({ animate: options.animate }, options.zoom);
                options.pan = extend({ animate: options.animate, duration: options.duration }, options.pan);
              }
              var moved = this._zoom !== zoom2 ? this._tryAnimatedZoom && this._tryAnimatedZoom(center, zoom2, options.zoom) : this._tryAnimatedPan(center, options.pan);
              if (moved) {
                clearTimeout(this._sizeTimer);
                return this;
              }
            }
            this._resetView(center, zoom2, options.pan && options.pan.noMoveStart);
            return this;
          },
          // @method setZoom(zoom: Number, options?: Zoom/pan options): this
          // Sets the zoom of the map.
          setZoom: function(zoom2, options) {
            if (!this._loaded) {
              this._zoom = zoom2;
              return this;
            }
            return this.setView(this.getCenter(), zoom2, { zoom: options });
          },
          // @method zoomIn(delta?: Number, options?: Zoom options): this
          // Increases the zoom of the map by `delta` ([`zoomDelta`](#map-zoomdelta) by default).
          zoomIn: function(delta, options) {
            delta = delta || (Browser.any3d ? this.options.zoomDelta : 1);
            return this.setZoom(this._zoom + delta, options);
          },
          // @method zoomOut(delta?: Number, options?: Zoom options): this
          // Decreases the zoom of the map by `delta` ([`zoomDelta`](#map-zoomdelta) by default).
          zoomOut: function(delta, options) {
            delta = delta || (Browser.any3d ? this.options.zoomDelta : 1);
            return this.setZoom(this._zoom - delta, options);
          },
          // @method setZoomAround(latlng: LatLng, zoom: Number, options: Zoom options): this
          // Zooms the map while keeping a specified geographical point on the map
          // stationary (e.g. used internally for scroll zoom and double-click zoom).
          // @alternative
          // @method setZoomAround(offset: Point, zoom: Number, options: Zoom options): this
          // Zooms the map while keeping a specified pixel on the map (relative to the top-left corner) stationary.
          setZoomAround: function(latlng, zoom2, options) {
            var scale2 = this.getZoomScale(zoom2), viewHalf = this.getSize().divideBy(2), containerPoint = latlng instanceof Point ? latlng : this.latLngToContainerPoint(latlng), centerOffset = containerPoint.subtract(viewHalf).multiplyBy(1 - 1 / scale2), newCenter = this.containerPointToLatLng(viewHalf.add(centerOffset));
            return this.setView(newCenter, zoom2, { zoom: options });
          },
          _getBoundsCenterZoom: function(bounds, options) {
            options = options || {};
            bounds = bounds.getBounds ? bounds.getBounds() : toLatLngBounds(bounds);
            var paddingTL = toPoint(options.paddingTopLeft || options.padding || [0, 0]), paddingBR = toPoint(options.paddingBottomRight || options.padding || [0, 0]), zoom2 = this.getBoundsZoom(bounds, false, paddingTL.add(paddingBR));
            zoom2 = typeof options.maxZoom === "number" ? Math.min(options.maxZoom, zoom2) : zoom2;
            if (zoom2 === Infinity) {
              return {
                center: bounds.getCenter(),
                zoom: zoom2
              };
            }
            var paddingOffset = paddingBR.subtract(paddingTL).divideBy(2), swPoint = this.project(bounds.getSouthWest(), zoom2), nePoint = this.project(bounds.getNorthEast(), zoom2), center = this.unproject(swPoint.add(nePoint).divideBy(2).add(paddingOffset), zoom2);
            return {
              center,
              zoom: zoom2
            };
          },
          // @method fitBounds(bounds: LatLngBounds, options?: fitBounds options): this
          // Sets a map view that contains the given geographical bounds with the
          // maximum zoom level possible.
          fitBounds: function(bounds, options) {
            bounds = toLatLngBounds(bounds);
            if (!bounds.isValid()) {
              throw new Error("Bounds are not valid.");
            }
            var target = this._getBoundsCenterZoom(bounds, options);
            return this.setView(target.center, target.zoom, options);
          },
          // @method fitWorld(options?: fitBounds options): this
          // Sets a map view that mostly contains the whole world with the maximum
          // zoom level possible.
          fitWorld: function(options) {
            return this.fitBounds([[-90, -180], [90, 180]], options);
          },
          // @method panTo(latlng: LatLng, options?: Pan options): this
          // Pans the map to a given center.
          panTo: function(center, options) {
            return this.setView(center, this._zoom, { pan: options });
          },
          // @method panBy(offset: Point, options?: Pan options): this
          // Pans the map by a given number of pixels (animated).
          panBy: function(offset, options) {
            offset = toPoint(offset).round();
            options = options || {};
            if (!offset.x && !offset.y) {
              return this.fire("moveend");
            }
            if (options.animate !== true && !this.getSize().contains(offset)) {
              this._resetView(this.unproject(this.project(this.getCenter()).add(offset)), this.getZoom());
              return this;
            }
            if (!this._panAnim) {
              this._panAnim = new PosAnimation();
              this._panAnim.on({
                "step": this._onPanTransitionStep,
                "end": this._onPanTransitionEnd
              }, this);
            }
            if (!options.noMoveStart) {
              this.fire("movestart");
            }
            if (options.animate !== false) {
              addClass(this._mapPane, "leaflet-pan-anim");
              var newPos = this._getMapPanePos().subtract(offset).round();
              this._panAnim.run(this._mapPane, newPos, options.duration || 0.25, options.easeLinearity);
            } else {
              this._rawPanBy(offset);
              this.fire("move").fire("moveend");
            }
            return this;
          },
          // @method flyTo(latlng: LatLng, zoom?: Number, options?: Zoom/pan options): this
          // Sets the view of the map (geographical center and zoom) performing a smooth
          // pan-zoom animation.
          flyTo: function(targetCenter, targetZoom, options) {
            options = options || {};
            if (options.animate === false || !Browser.any3d) {
              return this.setView(targetCenter, targetZoom, options);
            }
            this._stop();
            var from = this.project(this.getCenter()), to = this.project(targetCenter), size = this.getSize(), startZoom = this._zoom;
            targetCenter = toLatLng(targetCenter);
            targetZoom = targetZoom === void 0 ? startZoom : targetZoom;
            var w0 = Math.max(size.x, size.y), w1 = w0 * this.getZoomScale(startZoom, targetZoom), u1 = to.distanceTo(from) || 1, rho = 1.42, rho2 = rho * rho;
            function r(i) {
              var s1 = i ? -1 : 1, s2 = i ? w1 : w0, t1 = w1 * w1 - w0 * w0 + s1 * rho2 * rho2 * u1 * u1, b1 = 2 * s2 * rho2 * u1, b = t1 / b1, sq = Math.sqrt(b * b + 1) - b;
              var log = sq < 1e-9 ? -18 : Math.log(sq);
              return log;
            }
            function sinh(n) {
              return (Math.exp(n) - Math.exp(-n)) / 2;
            }
            function cosh(n) {
              return (Math.exp(n) + Math.exp(-n)) / 2;
            }
            function tanh(n) {
              return sinh(n) / cosh(n);
            }
            var r0 = r(0);
            function w(s) {
              return w0 * (cosh(r0) / cosh(r0 + rho * s));
            }
            function u(s) {
              return w0 * (cosh(r0) * tanh(r0 + rho * s) - sinh(r0)) / rho2;
            }
            function easeOut(t) {
              return 1 - Math.pow(1 - t, 1.5);
            }
            var start = Date.now(), S = (r(1) - r0) / rho, duration = options.duration ? 1e3 * options.duration : 1e3 * S * 0.8;
            function frame() {
              var t = (Date.now() - start) / duration, s = easeOut(t) * S;
              if (t <= 1) {
                this._flyToFrame = requestAnimFrame(frame, this);
                this._move(
                  this.unproject(from.add(to.subtract(from).multiplyBy(u(s) / u1)), startZoom),
                  this.getScaleZoom(w0 / w(s), startZoom),
                  { flyTo: true }
                );
              } else {
                this._move(targetCenter, targetZoom)._moveEnd(true);
              }
            }
            this._moveStart(true, options.noMoveStart);
            frame.call(this);
            return this;
          },
          // @method flyToBounds(bounds: LatLngBounds, options?: fitBounds options): this
          // Sets the view of the map with a smooth animation like [`flyTo`](#map-flyto),
          // but takes a bounds parameter like [`fitBounds`](#map-fitbounds).
          flyToBounds: function(bounds, options) {
            var target = this._getBoundsCenterZoom(bounds, options);
            return this.flyTo(target.center, target.zoom, options);
          },
          // @method setMaxBounds(bounds: LatLngBounds): this
          // Restricts the map view to the given bounds (see the [maxBounds](#map-maxbounds) option).
          setMaxBounds: function(bounds) {
            bounds = toLatLngBounds(bounds);
            if (this.listens("moveend", this._panInsideMaxBounds)) {
              this.off("moveend", this._panInsideMaxBounds);
            }
            if (!bounds.isValid()) {
              this.options.maxBounds = null;
              return this;
            }
            this.options.maxBounds = bounds;
            if (this._loaded) {
              this._panInsideMaxBounds();
            }
            return this.on("moveend", this._panInsideMaxBounds);
          },
          // @method setMinZoom(zoom: Number): this
          // Sets the lower limit for the available zoom levels (see the [minZoom](#map-minzoom) option).
          setMinZoom: function(zoom2) {
            var oldZoom = this.options.minZoom;
            this.options.minZoom = zoom2;
            if (this._loaded && oldZoom !== zoom2) {
              this.fire("zoomlevelschange");
              if (this.getZoom() < this.options.minZoom) {
                return this.setZoom(zoom2);
              }
            }
            return this;
          },
          // @method setMaxZoom(zoom: Number): this
          // Sets the upper limit for the available zoom levels (see the [maxZoom](#map-maxzoom) option).
          setMaxZoom: function(zoom2) {
            var oldZoom = this.options.maxZoom;
            this.options.maxZoom = zoom2;
            if (this._loaded && oldZoom !== zoom2) {
              this.fire("zoomlevelschange");
              if (this.getZoom() > this.options.maxZoom) {
                return this.setZoom(zoom2);
              }
            }
            return this;
          },
          // @method panInsideBounds(bounds: LatLngBounds, options?: Pan options): this
          // Pans the map to the closest view that would lie inside the given bounds (if it's not already), controlling the animation using the options specific, if any.
          panInsideBounds: function(bounds, options) {
            this._enforcingBounds = true;
            var center = this.getCenter(), newCenter = this._limitCenter(center, this._zoom, toLatLngBounds(bounds));
            if (!center.equals(newCenter)) {
              this.panTo(newCenter, options);
            }
            this._enforcingBounds = false;
            return this;
          },
          // @method panInside(latlng: LatLng, options?: padding options): this
          // Pans the map the minimum amount to make the `latlng` visible. Use
          // padding options to fit the display to more restricted bounds.
          // If `latlng` is already within the (optionally padded) display bounds,
          // the map will not be panned.
          panInside: function(latlng, options) {
            options = options || {};
            var paddingTL = toPoint(options.paddingTopLeft || options.padding || [0, 0]), paddingBR = toPoint(options.paddingBottomRight || options.padding || [0, 0]), pixelCenter = this.project(this.getCenter()), pixelPoint = this.project(latlng), pixelBounds = this.getPixelBounds(), paddedBounds = toBounds([pixelBounds.min.add(paddingTL), pixelBounds.max.subtract(paddingBR)]), paddedSize = paddedBounds.getSize();
            if (!paddedBounds.contains(pixelPoint)) {
              this._enforcingBounds = true;
              var centerOffset = pixelPoint.subtract(paddedBounds.getCenter());
              var offset = paddedBounds.extend(pixelPoint).getSize().subtract(paddedSize);
              pixelCenter.x += centerOffset.x < 0 ? -offset.x : offset.x;
              pixelCenter.y += centerOffset.y < 0 ? -offset.y : offset.y;
              this.panTo(this.unproject(pixelCenter), options);
              this._enforcingBounds = false;
            }
            return this;
          },
          // @method invalidateSize(options: Zoom/pan options): this
          // Checks if the map container size changed and updates the map if so —
          // call it after you've changed the map size dynamically, also animating
          // pan by default. If `options.pan` is `false`, panning will not occur.
          // If `options.debounceMoveend` is `true`, it will delay `moveend` event so
          // that it doesn't happen often even if the method is called many
          // times in a row.
          // @alternative
          // @method invalidateSize(animate: Boolean): this
          // Checks if the map container size changed and updates the map if so —
          // call it after you've changed the map size dynamically, also animating
          // pan by default.
          invalidateSize: function(options) {
            if (!this._loaded) {
              return this;
            }
            options = extend({
              animate: false,
              pan: true
            }, options === true ? { animate: true } : options);
            var oldSize = this.getSize();
            this._sizeChanged = true;
            this._lastCenter = null;
            var newSize = this.getSize(), oldCenter = oldSize.divideBy(2).round(), newCenter = newSize.divideBy(2).round(), offset = oldCenter.subtract(newCenter);
            if (!offset.x && !offset.y) {
              return this;
            }
            if (options.animate && options.pan) {
              this.panBy(offset);
            } else {
              if (options.pan) {
                this._rawPanBy(offset);
              }
              this.fire("move");
              if (options.debounceMoveend) {
                clearTimeout(this._sizeTimer);
                this._sizeTimer = setTimeout(bind(this.fire, this, "moveend"), 200);
              } else {
                this.fire("moveend");
              }
            }
            return this.fire("resize", {
              oldSize,
              newSize
            });
          },
          // @section Methods for modifying map state
          // @method stop(): this
          // Stops the currently running `panTo` or `flyTo` animation, if any.
          stop: function() {
            this.setZoom(this._limitZoom(this._zoom));
            if (!this.options.zoomSnap) {
              this.fire("viewreset");
            }
            return this._stop();
          },
          // @section Geolocation methods
          // @method locate(options?: Locate options): this
          // Tries to locate the user using the Geolocation API, firing a [`locationfound`](#map-locationfound)
          // event with location data on success or a [`locationerror`](#map-locationerror) event on failure,
          // and optionally sets the map view to the user's location with respect to
          // detection accuracy (or to the world view if geolocation failed).
          // Note that, if your page doesn't use HTTPS, this method will fail in
          // modern browsers ([Chrome 50 and newer](https://sites.google.com/a/chromium.org/dev/Home/chromium-security/deprecating-powerful-features-on-insecure-origins))
          // See `Locate options` for more details.
          locate: function(options) {
            options = this._locateOptions = extend({
              timeout: 1e4,
              watch: false
              // setView: false
              // maxZoom: <Number>
              // maximumAge: 0
              // enableHighAccuracy: false
            }, options);
            if (!("geolocation" in navigator)) {
              this._handleGeolocationError({
                code: 0,
                message: "Geolocation not supported."
              });
              return this;
            }
            var onResponse = bind(this._handleGeolocationResponse, this), onError = bind(this._handleGeolocationError, this);
            if (options.watch) {
              this._locationWatchId = navigator.geolocation.watchPosition(onResponse, onError, options);
            } else {
              navigator.geolocation.getCurrentPosition(onResponse, onError, options);
            }
            return this;
          },
          // @method stopLocate(): this
          // Stops watching location previously initiated by `map.locate({watch: true})`
          // and aborts resetting the map view if map.locate was called with
          // `{setView: true}`.
          stopLocate: function() {
            if (navigator.geolocation && navigator.geolocation.clearWatch) {
              navigator.geolocation.clearWatch(this._locationWatchId);
            }
            if (this._locateOptions) {
              this._locateOptions.setView = false;
            }
            return this;
          },
          _handleGeolocationError: function(error) {
            if (!this._container._leaflet_id) {
              return;
            }
            var c = error.code, message = error.message || (c === 1 ? "permission denied" : c === 2 ? "position unavailable" : "timeout");
            if (this._locateOptions.setView && !this._loaded) {
              this.fitWorld();
            }
            this.fire("locationerror", {
              code: c,
              message: "Geolocation error: " + message + "."
            });
          },
          _handleGeolocationResponse: function(pos) {
            if (!this._container._leaflet_id) {
              return;
            }
            var lat = pos.coords.latitude, lng = pos.coords.longitude, latlng = new LatLng(lat, lng), bounds = latlng.toBounds(pos.coords.accuracy * 2), options = this._locateOptions;
            if (options.setView) {
              var zoom2 = this.getBoundsZoom(bounds);
              this.setView(latlng, options.maxZoom ? Math.min(zoom2, options.maxZoom) : zoom2);
            }
            var data = {
              latlng,
              bounds,
              timestamp: pos.timestamp
            };
            for (var i in pos.coords) {
              if (typeof pos.coords[i] === "number") {
                data[i] = pos.coords[i];
              }
            }
            this.fire("locationfound", data);
          },
          // TODO Appropriate docs section?
          // @section Other Methods
          // @method addHandler(name: String, HandlerClass: Function): this
          // Adds a new `Handler` to the map, given its name and constructor function.
          addHandler: function(name, HandlerClass) {
            if (!HandlerClass) {
              return this;
            }
            var handler = this[name] = new HandlerClass(this);
            this._handlers.push(handler);
            if (this.options[name]) {
              handler.enable();
            }
            return this;
          },
          // @method remove(): this
          // Destroys the map and clears all related event listeners.
          remove: function() {
            this._initEvents(true);
            if (this.options.maxBounds) {
              this.off("moveend", this._panInsideMaxBounds);
            }
            if (this._containerId !== this._container._leaflet_id) {
              throw new Error("Map container is being reused by another instance");
            }
            try {
              delete this._container._leaflet_id;
              delete this._containerId;
            } catch (e) {
              this._container._leaflet_id = void 0;
              this._containerId = void 0;
            }
            if (this._locationWatchId !== void 0) {
              this.stopLocate();
            }
            this._stop();
            remove(this._mapPane);
            if (this._clearControlPos) {
              this._clearControlPos();
            }
            if (this._resizeRequest) {
              cancelAnimFrame(this._resizeRequest);
              this._resizeRequest = null;
            }
            this._clearHandlers();
            if (this._loaded) {
              this.fire("unload");
            }
            var i;
            for (i in this._layers) {
              this._layers[i].remove();
            }
            for (i in this._panes) {
              remove(this._panes[i]);
            }
            this._layers = [];
            this._panes = [];
            delete this._mapPane;
            delete this._renderer;
            return this;
          },
          // @section Other Methods
          // @method createPane(name: String, container?: HTMLElement): HTMLElement
          // Creates a new [map pane](#map-pane) with the given name if it doesn't exist already,
          // then returns it. The pane is created as a child of `container`, or
          // as a child of the main map pane if not set.
          createPane: function(name, container) {
            var className = "leaflet-pane" + (name ? " leaflet-" + name.replace("Pane", "") + "-pane" : ""), pane = create$1("div", className, container || this._mapPane);
            if (name) {
              this._panes[name] = pane;
            }
            return pane;
          },
          // @section Methods for Getting Map State
          // @method getCenter(): LatLng
          // Returns the geographical center of the map view
          getCenter: function() {
            this._checkIfLoaded();
            if (this._lastCenter && !this._moved()) {
              return this._lastCenter.clone();
            }
            return this.layerPointToLatLng(this._getCenterLayerPoint());
          },
          // @method getZoom(): Number
          // Returns the current zoom level of the map view
          getZoom: function() {
            return this._zoom;
          },
          // @method getBounds(): LatLngBounds
          // Returns the geographical bounds visible in the current map view
          getBounds: function() {
            var bounds = this.getPixelBounds(), sw = this.unproject(bounds.getBottomLeft()), ne = this.unproject(bounds.getTopRight());
            return new LatLngBounds(sw, ne);
          },
          // @method getMinZoom(): Number
          // Returns the minimum zoom level of the map (if set in the `minZoom` option of the map or of any layers), or `0` by default.
          getMinZoom: function() {
            return this.options.minZoom === void 0 ? this._layersMinZoom || 0 : this.options.minZoom;
          },
          // @method getMaxZoom(): Number
          // Returns the maximum zoom level of the map (if set in the `maxZoom` option of the map or of any layers).
          getMaxZoom: function() {
            return this.options.maxZoom === void 0 ? this._layersMaxZoom === void 0 ? Infinity : this._layersMaxZoom : this.options.maxZoom;
          },
          // @method getBoundsZoom(bounds: LatLngBounds, inside?: Boolean, padding?: Point): Number
          // Returns the maximum zoom level on which the given bounds fit to the map
          // view in its entirety. If `inside` (optional) is set to `true`, the method
          // instead returns the minimum zoom level on which the map view fits into
          // the given bounds in its entirety.
          getBoundsZoom: function(bounds, inside, padding) {
            bounds = toLatLngBounds(bounds);
            padding = toPoint(padding || [0, 0]);
            var zoom2 = this.getZoom() || 0, min = this.getMinZoom(), max = this.getMaxZoom(), nw = bounds.getNorthWest(), se = bounds.getSouthEast(), size = this.getSize().subtract(padding), boundsSize = toBounds(this.project(se, zoom2), this.project(nw, zoom2)).getSize(), snap = Browser.any3d ? this.options.zoomSnap : 1, scalex = size.x / boundsSize.x, scaley = size.y / boundsSize.y, scale2 = inside ? Math.max(scalex, scaley) : Math.min(scalex, scaley);
            zoom2 = this.getScaleZoom(scale2, zoom2);
            if (snap) {
              zoom2 = Math.round(zoom2 / (snap / 100)) * (snap / 100);
              zoom2 = inside ? Math.ceil(zoom2 / snap) * snap : Math.floor(zoom2 / snap) * snap;
            }
            return Math.max(min, Math.min(max, zoom2));
          },
          // @method getSize(): Point
          // Returns the current size of the map container (in pixels).
          getSize: function() {
            if (!this._size || this._sizeChanged) {
              this._size = new Point(
                this._container.clientWidth || 0,
                this._container.clientHeight || 0
              );
              this._sizeChanged = false;
            }
            return this._size.clone();
          },
          // @method getPixelBounds(): Bounds
          // Returns the bounds of the current map view in projected pixel
          // coordinates (sometimes useful in layer and overlay implementations).
          getPixelBounds: function(center, zoom2) {
            var topLeftPoint = this._getTopLeftPoint(center, zoom2);
            return new Bounds(topLeftPoint, topLeftPoint.add(this.getSize()));
          },
          // TODO: Check semantics - isn't the pixel origin the 0,0 coord relative to
          // the map pane? "left point of the map layer" can be confusing, specially
          // since there can be negative offsets.
          // @method getPixelOrigin(): Point
          // Returns the projected pixel coordinates of the top left point of
          // the map layer (useful in custom layer and overlay implementations).
          getPixelOrigin: function() {
            this._checkIfLoaded();
            return this._pixelOrigin;
          },
          // @method getPixelWorldBounds(zoom?: Number): Bounds
          // Returns the world's bounds in pixel coordinates for zoom level `zoom`.
          // If `zoom` is omitted, the map's current zoom level is used.
          getPixelWorldBounds: function(zoom2) {
            return this.options.crs.getProjectedBounds(zoom2 === void 0 ? this.getZoom() : zoom2);
          },
          // @section Other Methods
          // @method getPane(pane: String|HTMLElement): HTMLElement
          // Returns a [map pane](#map-pane), given its name or its HTML element (its identity).
          getPane: function(pane) {
            return typeof pane === "string" ? this._panes[pane] : pane;
          },
          // @method getPanes(): Object
          // Returns a plain object containing the names of all [panes](#map-pane) as keys and
          // the panes as values.
          getPanes: function() {
            return this._panes;
          },
          // @method getContainer: HTMLElement
          // Returns the HTML element that contains the map.
          getContainer: function() {
            return this._container;
          },
          // @section Conversion Methods
          // @method getZoomScale(toZoom: Number, fromZoom: Number): Number
          // Returns the scale factor to be applied to a map transition from zoom level
          // `fromZoom` to `toZoom`. Used internally to help with zoom animations.
          getZoomScale: function(toZoom, fromZoom) {
            var crs = this.options.crs;
            fromZoom = fromZoom === void 0 ? this._zoom : fromZoom;
            return crs.scale(toZoom) / crs.scale(fromZoom);
          },
          // @method getScaleZoom(scale: Number, fromZoom: Number): Number
          // Returns the zoom level that the map would end up at, if it is at `fromZoom`
          // level and everything is scaled by a factor of `scale`. Inverse of
          // [`getZoomScale`](#map-getZoomScale).
          getScaleZoom: function(scale2, fromZoom) {
            var crs = this.options.crs;
            fromZoom = fromZoom === void 0 ? this._zoom : fromZoom;
            var zoom2 = crs.zoom(scale2 * crs.scale(fromZoom));
            return isNaN(zoom2) ? Infinity : zoom2;
          },
          // @method project(latlng: LatLng, zoom: Number): Point
          // Projects a geographical coordinate `LatLng` according to the projection
          // of the map's CRS, then scales it according to `zoom` and the CRS's
          // `Transformation`. The result is pixel coordinate relative to
          // the CRS origin.
          project: function(latlng, zoom2) {
            zoom2 = zoom2 === void 0 ? this._zoom : zoom2;
            return this.options.crs.latLngToPoint(toLatLng(latlng), zoom2);
          },
          // @method unproject(point: Point, zoom: Number): LatLng
          // Inverse of [`project`](#map-project).
          unproject: function(point, zoom2) {
            zoom2 = zoom2 === void 0 ? this._zoom : zoom2;
            return this.options.crs.pointToLatLng(toPoint(point), zoom2);
          },
          // @method layerPointToLatLng(point: Point): LatLng
          // Given a pixel coordinate relative to the [origin pixel](#map-getpixelorigin),
          // returns the corresponding geographical coordinate (for the current zoom level).
          layerPointToLatLng: function(point) {
            var projectedPoint = toPoint(point).add(this.getPixelOrigin());
            return this.unproject(projectedPoint);
          },
          // @method latLngToLayerPoint(latlng: LatLng): Point
          // Given a geographical coordinate, returns the corresponding pixel coordinate
          // relative to the [origin pixel](#map-getpixelorigin).
          latLngToLayerPoint: function(latlng) {
            var projectedPoint = this.project(toLatLng(latlng))._round();
            return projectedPoint._subtract(this.getPixelOrigin());
          },
          // @method wrapLatLng(latlng: LatLng): LatLng
          // Returns a `LatLng` where `lat` and `lng` has been wrapped according to the
          // map's CRS's `wrapLat` and `wrapLng` properties, if they are outside the
          // CRS's bounds.
          // By default this means longitude is wrapped around the dateline so its
          // value is between -180 and +180 degrees.
          wrapLatLng: function(latlng) {
            return this.options.crs.wrapLatLng(toLatLng(latlng));
          },
          // @method wrapLatLngBounds(bounds: LatLngBounds): LatLngBounds
          // Returns a `LatLngBounds` with the same size as the given one, ensuring that
          // its center is within the CRS's bounds.
          // By default this means the center longitude is wrapped around the dateline so its
          // value is between -180 and +180 degrees, and the majority of the bounds
          // overlaps the CRS's bounds.
          wrapLatLngBounds: function(latlng) {
            return this.options.crs.wrapLatLngBounds(toLatLngBounds(latlng));
          },
          // @method distance(latlng1: LatLng, latlng2: LatLng): Number
          // Returns the distance between two geographical coordinates according to
          // the map's CRS. By default this measures distance in meters.
          distance: function(latlng1, latlng2) {
            return this.options.crs.distance(toLatLng(latlng1), toLatLng(latlng2));
          },
          // @method containerPointToLayerPoint(point: Point): Point
          // Given a pixel coordinate relative to the map container, returns the corresponding
          // pixel coordinate relative to the [origin pixel](#map-getpixelorigin).
          containerPointToLayerPoint: function(point) {
            return toPoint(point).subtract(this._getMapPanePos());
          },
          // @method layerPointToContainerPoint(point: Point): Point
          // Given a pixel coordinate relative to the [origin pixel](#map-getpixelorigin),
          // returns the corresponding pixel coordinate relative to the map container.
          layerPointToContainerPoint: function(point) {
            return toPoint(point).add(this._getMapPanePos());
          },
          // @method containerPointToLatLng(point: Point): LatLng
          // Given a pixel coordinate relative to the map container, returns
          // the corresponding geographical coordinate (for the current zoom level).
          containerPointToLatLng: function(point) {
            var layerPoint = this.containerPointToLayerPoint(toPoint(point));
            return this.layerPointToLatLng(layerPoint);
          },
          // @method latLngToContainerPoint(latlng: LatLng): Point
          // Given a geographical coordinate, returns the corresponding pixel coordinate
          // relative to the map container.
          latLngToContainerPoint: function(latlng) {
            return this.layerPointToContainerPoint(this.latLngToLayerPoint(toLatLng(latlng)));
          },
          // @method mouseEventToContainerPoint(ev: MouseEvent): Point
          // Given a MouseEvent object, returns the pixel coordinate relative to the
          // map container where the event took place.
          mouseEventToContainerPoint: function(e) {
            return getMousePosition(e, this._container);
          },
          // @method mouseEventToLayerPoint(ev: MouseEvent): Point
          // Given a MouseEvent object, returns the pixel coordinate relative to
          // the [origin pixel](#map-getpixelorigin) where the event took place.
          mouseEventToLayerPoint: function(e) {
            return this.containerPointToLayerPoint(this.mouseEventToContainerPoint(e));
          },
          // @method mouseEventToLatLng(ev: MouseEvent): LatLng
          // Given a MouseEvent object, returns geographical coordinate where the
          // event took place.
          mouseEventToLatLng: function(e) {
            return this.layerPointToLatLng(this.mouseEventToLayerPoint(e));
          },
          // map initialization methods
          _initContainer: function(id) {
            var container = this._container = get(id);
            if (!container) {
              throw new Error("Map container not found.");
            } else if (container._leaflet_id) {
              throw new Error("Map container is already initialized.");
            }
            on(container, "scroll", this._onScroll, this);
            this._containerId = stamp(container);
          },
          _initLayout: function() {
            var container = this._container;
            this._fadeAnimated = this.options.fadeAnimation && Browser.any3d;
            addClass(container, "leaflet-container" + (Browser.touch ? " leaflet-touch" : "") + (Browser.retina ? " leaflet-retina" : "") + (Browser.ielt9 ? " leaflet-oldie" : "") + (Browser.safari ? " leaflet-safari" : "") + (this._fadeAnimated ? " leaflet-fade-anim" : ""));
            var position = getStyle(container, "position");
            if (position !== "absolute" && position !== "relative" && position !== "fixed" && position !== "sticky") {
              container.style.position = "relative";
            }
            this._initPanes();
            if (this._initControlPos) {
              this._initControlPos();
            }
          },
          _initPanes: function() {
            var panes = this._panes = {};
            this._paneRenderers = {};
            this._mapPane = this.createPane("mapPane", this._container);
            setPosition(this._mapPane, new Point(0, 0));
            this.createPane("tilePane");
            this.createPane("overlayPane");
            this.createPane("shadowPane");
            this.createPane("markerPane");
            this.createPane("tooltipPane");
            this.createPane("popupPane");
            if (!this.options.markerZoomAnimation) {
              addClass(panes.markerPane, "leaflet-zoom-hide");
              addClass(panes.shadowPane, "leaflet-zoom-hide");
            }
          },
          // private methods that modify map state
          // @section Map state change events
          _resetView: function(center, zoom2, noMoveStart) {
            setPosition(this._mapPane, new Point(0, 0));
            var loading = !this._loaded;
            this._loaded = true;
            zoom2 = this._limitZoom(zoom2);
            this.fire("viewprereset");
            var zoomChanged = this._zoom !== zoom2;
            this._moveStart(zoomChanged, noMoveStart)._move(center, zoom2)._moveEnd(zoomChanged);
            this.fire("viewreset");
            if (loading) {
              this.fire("load");
            }
          },
          _moveStart: function(zoomChanged, noMoveStart) {
            if (zoomChanged) {
              this.fire("zoomstart");
            }
            if (!noMoveStart) {
              this.fire("movestart");
            }
            return this;
          },
          _move: function(center, zoom2, data, supressEvent) {
            if (zoom2 === void 0) {
              zoom2 = this._zoom;
            }
            var zoomChanged = this._zoom !== zoom2;
            this._zoom = zoom2;
            this._lastCenter = center;
            this._pixelOrigin = this._getNewPixelOrigin(center);
            if (!supressEvent) {
              if (zoomChanged || data && data.pinch) {
                this.fire("zoom", data);
              }
              this.fire("move", data);
            } else if (data && data.pinch) {
              this.fire("zoom", data);
            }
            return this;
          },
          _moveEnd: function(zoomChanged) {
            if (zoomChanged) {
              this.fire("zoomend");
            }
            return this.fire("moveend");
          },
          _stop: function() {
            cancelAnimFrame(this._flyToFrame);
            if (this._panAnim) {
              this._panAnim.stop();
            }
            return this;
          },
          _rawPanBy: function(offset) {
            setPosition(this._mapPane, this._getMapPanePos().subtract(offset));
          },
          _getZoomSpan: function() {
            return this.getMaxZoom() - this.getMinZoom();
          },
          _panInsideMaxBounds: function() {
            if (!this._enforcingBounds) {
              this.panInsideBounds(this.options.maxBounds);
            }
          },
          _checkIfLoaded: function() {
            if (!this._loaded) {
              throw new Error("Set map center and zoom first.");
            }
          },
          // DOM event handling
          // @section Interaction events
          _initEvents: function(remove2) {
            this._targets = {};
            this._targets[stamp(this._container)] = this;
            var onOff = remove2 ? off : on;
            onOff(this._container, "click dblclick mousedown mouseup mouseover mouseout mousemove contextmenu keypress keydown keyup", this._handleDOMEvent, this);
            if (this.options.trackResize) {
              onOff(window, "resize", this._onResize, this);
            }
            if (Browser.any3d && this.options.transform3DLimit) {
              (remove2 ? this.off : this.on).call(this, "moveend", this._onMoveEnd);
            }
          },
          _onResize: function() {
            cancelAnimFrame(this._resizeRequest);
            this._resizeRequest = requestAnimFrame(
              function() {
                this.invalidateSize({ debounceMoveend: true });
              },
              this
            );
          },
          _onScroll: function() {
            this._container.scrollTop = 0;
            this._container.scrollLeft = 0;
          },
          _onMoveEnd: function() {
            var pos = this._getMapPanePos();
            if (Math.max(Math.abs(pos.x), Math.abs(pos.y)) >= this.options.transform3DLimit) {
              this._resetView(this.getCenter(), this.getZoom());
            }
          },
          _findEventTargets: function(e, type2) {
            var targets = [], target, isHover = type2 === "mouseout" || type2 === "mouseover", src = e.target || e.srcElement, dragging = false;
            while (src) {
              target = this._targets[stamp(src)];
              if (target && (type2 === "click" || type2 === "preclick") && this._draggableMoved(target)) {
                dragging = true;
                break;
              }
              if (target && target.listens(type2, true)) {
                if (isHover && !isExternalTarget(src, e)) {
                  break;
                }
                targets.push(target);
                if (isHover) {
                  break;
                }
              }
              if (src === this._container) {
                break;
              }
              src = src.parentNode;
            }
            if (!targets.length && !dragging && !isHover && this.listens(type2, true)) {
              targets = [this];
            }
            return targets;
          },
          _isClickDisabled: function(el) {
            while (el && el !== this._container) {
              if (el["_leaflet_disable_click"]) {
                return true;
              }
              el = el.parentNode;
            }
          },
          _handleDOMEvent: function(e) {
            var el = e.target || e.srcElement;
            if (!this._loaded || el["_leaflet_disable_events"] || e.type === "click" && this._isClickDisabled(el)) {
              return;
            }
            var type2 = e.type;
            if (type2 === "mousedown") {
              preventOutline(el);
            }
            this._fireDOMEvent(e, type2);
          },
          _mouseEvents: ["click", "dblclick", "mouseover", "mouseout", "contextmenu"],
          _fireDOMEvent: function(e, type2, canvasTargets) {
            if (e.type === "click") {
              var synth = extend({}, e);
              synth.type = "preclick";
              this._fireDOMEvent(synth, synth.type, canvasTargets);
            }
            var targets = this._findEventTargets(e, type2);
            if (canvasTargets) {
              var filtered = [];
              for (var i = 0; i < canvasTargets.length; i++) {
                if (canvasTargets[i].listens(type2, true)) {
                  filtered.push(canvasTargets[i]);
                }
              }
              targets = filtered.concat(targets);
            }
            if (!targets.length) {
              return;
            }
            if (type2 === "contextmenu") {
              preventDefault(e);
            }
            var target = targets[0];
            var data = {
              originalEvent: e
            };
            if (e.type !== "keypress" && e.type !== "keydown" && e.type !== "keyup") {
              var isMarker = target.getLatLng && (!target._radius || target._radius <= 10);
              data.containerPoint = isMarker ? this.latLngToContainerPoint(target.getLatLng()) : this.mouseEventToContainerPoint(e);
              data.layerPoint = this.containerPointToLayerPoint(data.containerPoint);
              data.latlng = isMarker ? target.getLatLng() : this.layerPointToLatLng(data.layerPoint);
            }
            for (i = 0; i < targets.length; i++) {
              targets[i].fire(type2, data, true);
              if (data.originalEvent._stopped || targets[i].options.bubblingMouseEvents === false && indexOf(this._mouseEvents, type2) !== -1) {
                return;
              }
            }
          },
          _draggableMoved: function(obj) {
            obj = obj.dragging && obj.dragging.enabled() ? obj : this;
            return obj.dragging && obj.dragging.moved() || this.boxZoom && this.boxZoom.moved();
          },
          _clearHandlers: function() {
            for (var i = 0, len = this._handlers.length; i < len; i++) {
              this._handlers[i].disable();
            }
          },
          // @section Other Methods
          // @method whenReady(fn: Function, context?: Object): this
          // Runs the given function `fn` when the map gets initialized with
          // a view (center and zoom) and at least one layer, or immediately
          // if it's already initialized, optionally passing a function context.
          whenReady: function(callback, context) {
            if (this._loaded) {
              callback.call(context || this, { target: this });
            } else {
              this.on("load", callback, context);
            }
            return this;
          },
          // private methods for getting map state
          _getMapPanePos: function() {
            return getPosition(this._mapPane) || new Point(0, 0);
          },
          _moved: function() {
            var pos = this._getMapPanePos();
            return pos && !pos.equals([0, 0]);
          },
          _getTopLeftPoint: function(center, zoom2) {
            var pixelOrigin = center && zoom2 !== void 0 ? this._getNewPixelOrigin(center, zoom2) : this.getPixelOrigin();
            return pixelOrigin.subtract(this._getMapPanePos());
          },
          _getNewPixelOrigin: function(center, zoom2) {
            var viewHalf = this.getSize()._divideBy(2);
            return this.project(center, zoom2)._subtract(viewHalf)._add(this._getMapPanePos())._round();
          },
          _latLngToNewLayerPoint: function(latlng, zoom2, center) {
            var topLeft = this._getNewPixelOrigin(center, zoom2);
            return this.project(latlng, zoom2)._subtract(topLeft);
          },
          _latLngBoundsToNewLayerBounds: function(latLngBounds, zoom2, center) {
            var topLeft = this._getNewPixelOrigin(center, zoom2);
            return toBounds([
              this.project(latLngBounds.getSouthWest(), zoom2)._subtract(topLeft),
              this.project(latLngBounds.getNorthWest(), zoom2)._subtract(topLeft),
              this.project(latLngBounds.getSouthEast(), zoom2)._subtract(topLeft),
              this.project(latLngBounds.getNorthEast(), zoom2)._subtract(topLeft)
            ]);
          },
          // layer point of the current center
          _getCenterLayerPoint: function() {
            return this.containerPointToLayerPoint(this.getSize()._divideBy(2));
          },
          // offset of the specified place to the current center in pixels
          _getCenterOffset: function(latlng) {
            return this.latLngToLayerPoint(latlng).subtract(this._getCenterLayerPoint());
          },
          // adjust center for view to get inside bounds
          _limitCenter: function(center, zoom2, bounds) {
            if (!bounds) {
              return center;
            }
            var centerPoint = this.project(center, zoom2), viewHalf = this.getSize().divideBy(2), viewBounds = new Bounds(centerPoint.subtract(viewHalf), centerPoint.add(viewHalf)), offset = this._getBoundsOffset(viewBounds, bounds, zoom2);
            if (Math.abs(offset.x) <= 1 && Math.abs(offset.y) <= 1) {
              return center;
            }
            return this.unproject(centerPoint.add(offset), zoom2);
          },
          // adjust offset for view to get inside bounds
          _limitOffset: function(offset, bounds) {
            if (!bounds) {
              return offset;
            }
            var viewBounds = this.getPixelBounds(), newBounds = new Bounds(viewBounds.min.add(offset), viewBounds.max.add(offset));
            return offset.add(this._getBoundsOffset(newBounds, bounds));
          },
          // returns offset needed for pxBounds to get inside maxBounds at a specified zoom
          _getBoundsOffset: function(pxBounds, maxBounds, zoom2) {
            var projectedMaxBounds = toBounds(
              this.project(maxBounds.getNorthEast(), zoom2),
              this.project(maxBounds.getSouthWest(), zoom2)
            ), minOffset = projectedMaxBounds.min.subtract(pxBounds.min), maxOffset = projectedMaxBounds.max.subtract(pxBounds.max), dx = this._rebound(minOffset.x, -maxOffset.x), dy = this._rebound(minOffset.y, -maxOffset.y);
            return new Point(dx, dy);
          },
          _rebound: function(left, right) {
            return left + right > 0 ? Math.round(left - right) / 2 : Math.max(0, Math.ceil(left)) - Math.max(0, Math.floor(right));
          },
          _limitZoom: function(zoom2) {
            var min = this.getMinZoom(), max = this.getMaxZoom(), snap = Browser.any3d ? this.options.zoomSnap : 1;
            if (snap) {
              zoom2 = Math.round(zoom2 / snap) * snap;
            }
            return Math.max(min, Math.min(max, zoom2));
          },
          _onPanTransitionStep: function() {
            this.fire("move");
          },
          _onPanTransitionEnd: function() {
            removeClass(this._mapPane, "leaflet-pan-anim");
            this.fire("moveend");
          },
          _tryAnimatedPan: function(center, options) {
            var offset = this._getCenterOffset(center)._trunc();
            if ((options && options.animate) !== true && !this.getSize().contains(offset)) {
              return false;
            }
            this.panBy(offset, options);
            return true;
          },
          _createAnimProxy: function() {
            var proxy = this._proxy = create$1("div", "leaflet-proxy leaflet-zoom-animated");
            this._panes.mapPane.appendChild(proxy);
            this.on("zoomanim", function(e) {
              var prop = TRANSFORM, transform = this._proxy.style[prop];
              setTransform(this._proxy, this.project(e.center, e.zoom), this.getZoomScale(e.zoom, 1));
              if (transform === this._proxy.style[prop] && this._animatingZoom) {
                this._onZoomTransitionEnd();
              }
            }, this);
            this.on("load moveend", this._animMoveEnd, this);
            this._on("unload", this._destroyAnimProxy, this);
          },
          _destroyAnimProxy: function() {
            remove(this._proxy);
            this.off("load moveend", this._animMoveEnd, this);
            delete this._proxy;
          },
          _animMoveEnd: function() {
            var c = this.getCenter(), z = this.getZoom();
            setTransform(this._proxy, this.project(c, z), this.getZoomScale(z, 1));
          },
          _catchTransitionEnd: function(e) {
            if (this._animatingZoom && e.propertyName.indexOf("transform") >= 0) {
              this._onZoomTransitionEnd();
            }
          },
          _nothingToAnimate: function() {
            return !this._container.getElementsByClassName("leaflet-zoom-animated").length;
          },
          _tryAnimatedZoom: function(center, zoom2, options) {
            if (this._animatingZoom) {
              return true;
            }
            options = options || {};
            if (!this._zoomAnimated || options.animate === false || this._nothingToAnimate() || Math.abs(zoom2 - this._zoom) > this.options.zoomAnimationThreshold) {
              return false;
            }
            var scale2 = this.getZoomScale(zoom2), offset = this._getCenterOffset(center)._divideBy(1 - 1 / scale2);
            if (options.animate !== true && !this.getSize().contains(offset)) {
              return false;
            }
            requestAnimFrame(function() {
              this._moveStart(true, options.noMoveStart || false)._animateZoom(center, zoom2, true);
            }, this);
            return true;
          },
          _animateZoom: function(center, zoom2, startAnim, noUpdate) {
            if (!this._mapPane) {
              return;
            }
            if (startAnim) {
              this._animatingZoom = true;
              this._animateToCenter = center;
              this._animateToZoom = zoom2;
              addClass(this._mapPane, "leaflet-zoom-anim");
            }
            this.fire("zoomanim", {
              center,
              zoom: zoom2,
              noUpdate
            });
            if (!this._tempFireZoomEvent) {
              this._tempFireZoomEvent = this._zoom !== this._animateToZoom;
            }
            this._move(this._animateToCenter, this._animateToZoom, void 0, true);
            setTimeout(bind(this._onZoomTransitionEnd, this), 250);
          },
          _onZoomTransitionEnd: function() {
            if (!this._animatingZoom) {
              return;
            }
            if (this._mapPane) {
              removeClass(this._mapPane, "leaflet-zoom-anim");
            }
            this._animatingZoom = false;
            this._move(this._animateToCenter, this._animateToZoom, void 0, true);
            if (this._tempFireZoomEvent) {
              this.fire("zoom");
            }
            delete this._tempFireZoomEvent;
            this.fire("move");
            this._moveEnd(true);
          }
        });
        function createMap(id, options) {
          return new Map3(id, options);
        }
        var Control = Class.extend({
          // @section
          // @aka Control Options
          options: {
            // @option position: String = 'topright'
            // The position of the control (one of the map corners). Possible values are `'topleft'`,
            // `'topright'`, `'bottomleft'` or `'bottomright'`
            position: "topright"
          },
          initialize: function(options) {
            setOptions(this, options);
          },
          /* @section
           * Classes extending L.Control will inherit the following methods:
           *
           * @method getPosition: string
           * Returns the position of the control.
           */
          getPosition: function() {
            return this.options.position;
          },
          // @method setPosition(position: string): this
          // Sets the position of the control.
          setPosition: function(position) {
            var map2 = this._map;
            if (map2) {
              map2.removeControl(this);
            }
            this.options.position = position;
            if (map2) {
              map2.addControl(this);
            }
            return this;
          },
          // @method getContainer: HTMLElement
          // Returns the HTMLElement that contains the control.
          getContainer: function() {
            return this._container;
          },
          // @method addTo(map: Map): this
          // Adds the control to the given map.
          addTo: function(map2) {
            this.remove();
            this._map = map2;
            var container = this._container = this.onAdd(map2), pos = this.getPosition(), corner = map2._controlCorners[pos];
            addClass(container, "leaflet-control");
            if (pos.indexOf("bottom") !== -1) {
              corner.insertBefore(container, corner.firstChild);
            } else {
              corner.appendChild(container);
            }
            this._map.on("unload", this.remove, this);
            return this;
          },
          // @method remove: this
          // Removes the control from the map it is currently active on.
          remove: function() {
            if (!this._map) {
              return this;
            }
            remove(this._container);
            if (this.onRemove) {
              this.onRemove(this._map);
            }
            this._map.off("unload", this.remove, this);
            this._map = null;
            return this;
          },
          _refocusOnMap: function(e) {
            if (this._map && e && e.screenX > 0 && e.screenY > 0) {
              this._map.getContainer().focus();
            }
          }
        });
        var control = function(options) {
          return new Control(options);
        };
        Map3.include({
          // @method addControl(control: Control): this
          // Adds the given control to the map
          addControl: function(control2) {
            control2.addTo(this);
            return this;
          },
          // @method removeControl(control: Control): this
          // Removes the given control from the map
          removeControl: function(control2) {
            control2.remove();
            return this;
          },
          _initControlPos: function() {
            var corners = this._controlCorners = {}, l = "leaflet-", container = this._controlContainer = create$1("div", l + "control-container", this._container);
            function createCorner(vSide, hSide) {
              var className = l + vSide + " " + l + hSide;
              corners[vSide + hSide] = create$1("div", className, container);
            }
            createCorner("top", "left");
            createCorner("top", "right");
            createCorner("bottom", "left");
            createCorner("bottom", "right");
          },
          _clearControlPos: function() {
            for (var i in this._controlCorners) {
              remove(this._controlCorners[i]);
            }
            remove(this._controlContainer);
            delete this._controlCorners;
            delete this._controlContainer;
          }
        });
        var Layers = Control.extend({
          // @section
          // @aka Control.Layers options
          options: {
            // @option collapsed: Boolean = true
            // If `true`, the control will be collapsed into an icon and expanded on mouse hover, touch, or keyboard activation.
            collapsed: true,
            position: "topright",
            // @option autoZIndex: Boolean = true
            // If `true`, the control will assign zIndexes in increasing order to all of its layers so that the order is preserved when switching them on/off.
            autoZIndex: true,
            // @option hideSingleBase: Boolean = false
            // If `true`, the base layers in the control will be hidden when there is only one.
            hideSingleBase: false,
            // @option sortLayers: Boolean = false
            // Whether to sort the layers. When `false`, layers will keep the order
            // in which they were added to the control.
            sortLayers: false,
            // @option sortFunction: Function = *
            // A [compare function](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)
            // that will be used for sorting the layers, when `sortLayers` is `true`.
            // The function receives both the `L.Layer` instances and their names, as in
            // `sortFunction(layerA, layerB, nameA, nameB)`.
            // By default, it sorts layers alphabetically by their name.
            sortFunction: function(layerA, layerB, nameA, nameB) {
              return nameA < nameB ? -1 : nameB < nameA ? 1 : 0;
            }
          },
          initialize: function(baseLayers, overlays, options) {
            setOptions(this, options);
            this._layerControlInputs = [];
            this._layers = [];
            this._lastZIndex = 0;
            this._handlingClick = false;
            this._preventClick = false;
            for (var i in baseLayers) {
              this._addLayer(baseLayers[i], i);
            }
            for (i in overlays) {
              this._addLayer(overlays[i], i, true);
            }
          },
          onAdd: function(map2) {
            this._initLayout();
            this._update();
            this._map = map2;
            map2.on("zoomend", this._checkDisabledLayers, this);
            for (var i = 0; i < this._layers.length; i++) {
              this._layers[i].layer.on("add remove", this._onLayerChange, this);
            }
            return this._container;
          },
          addTo: function(map2) {
            Control.prototype.addTo.call(this, map2);
            return this._expandIfNotCollapsed();
          },
          onRemove: function() {
            this._map.off("zoomend", this._checkDisabledLayers, this);
            for (var i = 0; i < this._layers.length; i++) {
              this._layers[i].layer.off("add remove", this._onLayerChange, this);
            }
          },
          // @method addBaseLayer(layer: Layer, name: String): this
          // Adds a base layer (radio button entry) with the given name to the control.
          addBaseLayer: function(layer, name) {
            this._addLayer(layer, name);
            return this._map ? this._update() : this;
          },
          // @method addOverlay(layer: Layer, name: String): this
          // Adds an overlay (checkbox entry) with the given name to the control.
          addOverlay: function(layer, name) {
            this._addLayer(layer, name, true);
            return this._map ? this._update() : this;
          },
          // @method removeLayer(layer: Layer): this
          // Remove the given layer from the control.
          removeLayer: function(layer) {
            layer.off("add remove", this._onLayerChange, this);
            var obj = this._getLayer(stamp(layer));
            if (obj) {
              this._layers.splice(this._layers.indexOf(obj), 1);
            }
            return this._map ? this._update() : this;
          },
          // @method expand(): this
          // Expand the control container if collapsed.
          expand: function() {
            addClass(this._container, "leaflet-control-layers-expanded");
            this._section.style.height = null;
            var acceptableHeight = this._map.getSize().y - (this._container.offsetTop + 50);
            if (acceptableHeight < this._section.clientHeight) {
              addClass(this._section, "leaflet-control-layers-scrollbar");
              this._section.style.height = acceptableHeight + "px";
            } else {
              removeClass(this._section, "leaflet-control-layers-scrollbar");
            }
            this._checkDisabledLayers();
            return this;
          },
          // @method collapse(): this
          // Collapse the control container if expanded.
          collapse: function() {
            removeClass(this._container, "leaflet-control-layers-expanded");
            return this;
          },
          _initLayout: function() {
            var className = "leaflet-control-layers", container = this._container = create$1("div", className), collapsed = this.options.collapsed;
            container.setAttribute("aria-haspopup", true);
            disableClickPropagation(container);
            disableScrollPropagation(container);
            var section = this._section = create$1("section", className + "-list");
            if (collapsed) {
              this._map.on("click", this.collapse, this);
              on(container, {
                mouseenter: this._expandSafely,
                mouseleave: this.collapse
              }, this);
            }
            var link = this._layersLink = create$1("a", className + "-toggle", container);
            link.href = "#";
            link.title = "Layers";
            link.setAttribute("role", "button");
            on(link, {
              keydown: function(e) {
                if (e.keyCode === 13) {
                  this._expandSafely();
                }
              },
              // Certain screen readers intercept the key event and instead send a click event
              click: function(e) {
                preventDefault(e);
                this._expandSafely();
              }
            }, this);
            if (!collapsed) {
              this.expand();
            }
            this._baseLayersList = create$1("div", className + "-base", section);
            this._separator = create$1("div", className + "-separator", section);
            this._overlaysList = create$1("div", className + "-overlays", section);
            container.appendChild(section);
          },
          _getLayer: function(id) {
            for (var i = 0; i < this._layers.length; i++) {
              if (this._layers[i] && stamp(this._layers[i].layer) === id) {
                return this._layers[i];
              }
            }
          },
          _addLayer: function(layer, name, overlay) {
            if (this._map) {
              layer.on("add remove", this._onLayerChange, this);
            }
            this._layers.push({
              layer,
              name,
              overlay
            });
            if (this.options.sortLayers) {
              this._layers.sort(bind(function(a, b) {
                return this.options.sortFunction(a.layer, b.layer, a.name, b.name);
              }, this));
            }
            if (this.options.autoZIndex && layer.setZIndex) {
              this._lastZIndex++;
              layer.setZIndex(this._lastZIndex);
            }
            this._expandIfNotCollapsed();
          },
          _update: function() {
            if (!this._container) {
              return this;
            }
            empty(this._baseLayersList);
            empty(this._overlaysList);
            this._layerControlInputs = [];
            var baseLayersPresent, overlaysPresent, i, obj, baseLayersCount = 0;
            for (i = 0; i < this._layers.length; i++) {
              obj = this._layers[i];
              this._addItem(obj);
              overlaysPresent = overlaysPresent || obj.overlay;
              baseLayersPresent = baseLayersPresent || !obj.overlay;
              baseLayersCount += !obj.overlay ? 1 : 0;
            }
            if (this.options.hideSingleBase) {
              baseLayersPresent = baseLayersPresent && baseLayersCount > 1;
              this._baseLayersList.style.display = baseLayersPresent ? "" : "none";
            }
            this._separator.style.display = overlaysPresent && baseLayersPresent ? "" : "none";
            return this;
          },
          _onLayerChange: function(e) {
            if (!this._handlingClick) {
              this._update();
            }
            var obj = this._getLayer(stamp(e.target));
            var type2 = obj.overlay ? e.type === "add" ? "overlayadd" : "overlayremove" : e.type === "add" ? "baselayerchange" : null;
            if (type2) {
              this._map.fire(type2, obj);
            }
          },
          // IE7 bugs out if you create a radio dynamically, so you have to do it this hacky way (see https://stackoverflow.com/a/119079)
          _createRadioElement: function(name, checked) {
            var radioHtml = '<input type="radio" class="leaflet-control-layers-selector" name="' + name + '"' + (checked ? ' checked="checked"' : "") + "/>";
            var radioFragment = document.createElement("div");
            radioFragment.innerHTML = radioHtml;
            return radioFragment.firstChild;
          },
          _addItem: function(obj) {
            var label = document.createElement("label"), checked = this._map.hasLayer(obj.layer), input;
            if (obj.overlay) {
              input = document.createElement("input");
              input.type = "checkbox";
              input.className = "leaflet-control-layers-selector";
              input.defaultChecked = checked;
            } else {
              input = this._createRadioElement("leaflet-base-layers_" + stamp(this), checked);
            }
            this._layerControlInputs.push(input);
            input.layerId = stamp(obj.layer);
            on(input, "click", this._onInputClick, this);
            var name = document.createElement("span");
            name.innerHTML = " " + obj.name;
            var holder = document.createElement("span");
            label.appendChild(holder);
            holder.appendChild(input);
            holder.appendChild(name);
            var container = obj.overlay ? this._overlaysList : this._baseLayersList;
            container.appendChild(label);
            this._checkDisabledLayers();
            return label;
          },
          _onInputClick: function() {
            if (this._preventClick) {
              return;
            }
            var inputs = this._layerControlInputs, input, layer;
            var addedLayers = [], removedLayers = [];
            this._handlingClick = true;
            for (var i = inputs.length - 1; i >= 0; i--) {
              input = inputs[i];
              layer = this._getLayer(input.layerId).layer;
              if (input.checked) {
                addedLayers.push(layer);
              } else if (!input.checked) {
                removedLayers.push(layer);
              }
            }
            for (i = 0; i < removedLayers.length; i++) {
              if (this._map.hasLayer(removedLayers[i])) {
                this._map.removeLayer(removedLayers[i]);
              }
            }
            for (i = 0; i < addedLayers.length; i++) {
              if (!this._map.hasLayer(addedLayers[i])) {
                this._map.addLayer(addedLayers[i]);
              }
            }
            this._handlingClick = false;
            this._refocusOnMap();
          },
          _checkDisabledLayers: function() {
            var inputs = this._layerControlInputs, input, layer, zoom2 = this._map.getZoom();
            for (var i = inputs.length - 1; i >= 0; i--) {
              input = inputs[i];
              layer = this._getLayer(input.layerId).layer;
              input.disabled = layer.options.minZoom !== void 0 && zoom2 < layer.options.minZoom || layer.options.maxZoom !== void 0 && zoom2 > layer.options.maxZoom;
            }
          },
          _expandIfNotCollapsed: function() {
            if (this._map && !this.options.collapsed) {
              this.expand();
            }
            return this;
          },
          _expandSafely: function() {
            var section = this._section;
            this._preventClick = true;
            on(section, "click", preventDefault);
            this.expand();
            var that = this;
            setTimeout(function() {
              off(section, "click", preventDefault);
              that._preventClick = false;
            });
          }
        });
        var layers = function(baseLayers, overlays, options) {
          return new Layers(baseLayers, overlays, options);
        };
        var Zoom = Control.extend({
          // @section
          // @aka Control.Zoom options
          options: {
            position: "topleft",
            // @option zoomInText: String = '<span aria-hidden="true">+</span>'
            // The text set on the 'zoom in' button.
            zoomInText: '<span aria-hidden="true">+</span>',
            // @option zoomInTitle: String = 'Zoom in'
            // The title set on the 'zoom in' button.
            zoomInTitle: "Zoom in",
            // @option zoomOutText: String = '<span aria-hidden="true">&#x2212;</span>'
            // The text set on the 'zoom out' button.
            zoomOutText: '<span aria-hidden="true">&#x2212;</span>',
            // @option zoomOutTitle: String = 'Zoom out'
            // The title set on the 'zoom out' button.
            zoomOutTitle: "Zoom out"
          },
          onAdd: function(map2) {
            var zoomName = "leaflet-control-zoom", container = create$1("div", zoomName + " leaflet-bar"), options = this.options;
            this._zoomInButton = this._createButton(
              options.zoomInText,
              options.zoomInTitle,
              zoomName + "-in",
              container,
              this._zoomIn
            );
            this._zoomOutButton = this._createButton(
              options.zoomOutText,
              options.zoomOutTitle,
              zoomName + "-out",
              container,
              this._zoomOut
            );
            this._updateDisabled();
            map2.on("zoomend zoomlevelschange", this._updateDisabled, this);
            return container;
          },
          onRemove: function(map2) {
            map2.off("zoomend zoomlevelschange", this._updateDisabled, this);
          },
          disable: function() {
            this._disabled = true;
            this._updateDisabled();
            return this;
          },
          enable: function() {
            this._disabled = false;
            this._updateDisabled();
            return this;
          },
          _zoomIn: function(e) {
            if (!this._disabled && this._map._zoom < this._map.getMaxZoom()) {
              this._map.zoomIn(this._map.options.zoomDelta * (e.shiftKey ? 3 : 1));
            }
          },
          _zoomOut: function(e) {
            if (!this._disabled && this._map._zoom > this._map.getMinZoom()) {
              this._map.zoomOut(this._map.options.zoomDelta * (e.shiftKey ? 3 : 1));
            }
          },
          _createButton: function(html, title, className, container, fn) {
            var link = create$1("a", className, container);
            link.innerHTML = html;
            link.href = "#";
            link.title = title;
            link.setAttribute("role", "button");
            link.setAttribute("aria-label", title);
            disableClickPropagation(link);
            on(link, "click", stop);
            on(link, "click", fn, this);
            on(link, "click", this._refocusOnMap, this);
            return link;
          },
          _updateDisabled: function() {
            var map2 = this._map, className = "leaflet-disabled";
            removeClass(this._zoomInButton, className);
            removeClass(this._zoomOutButton, className);
            this._zoomInButton.setAttribute("aria-disabled", "false");
            this._zoomOutButton.setAttribute("aria-disabled", "false");
            if (this._disabled || map2._zoom === map2.getMinZoom()) {
              addClass(this._zoomOutButton, className);
              this._zoomOutButton.setAttribute("aria-disabled", "true");
            }
            if (this._disabled || map2._zoom === map2.getMaxZoom()) {
              addClass(this._zoomInButton, className);
              this._zoomInButton.setAttribute("aria-disabled", "true");
            }
          }
        });
        Map3.mergeOptions({
          zoomControl: true
        });
        Map3.addInitHook(function() {
          if (this.options.zoomControl) {
            this.zoomControl = new Zoom();
            this.addControl(this.zoomControl);
          }
        });
        var zoom = function(options) {
          return new Zoom(options);
        };
        var Scale = Control.extend({
          // @section
          // @aka Control.Scale options
          options: {
            position: "bottomleft",
            // @option maxWidth: Number = 100
            // Maximum width of the control in pixels. The width is set dynamically to show round values (e.g. 100, 200, 500).
            maxWidth: 100,
            // @option metric: Boolean = True
            // Whether to show the metric scale line (m/km).
            metric: true,
            // @option imperial: Boolean = True
            // Whether to show the imperial scale line (mi/ft).
            imperial: true
            // @option updateWhenIdle: Boolean = false
            // If `true`, the control is updated on [`moveend`](#map-moveend), otherwise it's always up-to-date (updated on [`move`](#map-move)).
          },
          onAdd: function(map2) {
            var className = "leaflet-control-scale", container = create$1("div", className), options = this.options;
            this._addScales(options, className + "-line", container);
            map2.on(options.updateWhenIdle ? "moveend" : "move", this._update, this);
            map2.whenReady(this._update, this);
            return container;
          },
          onRemove: function(map2) {
            map2.off(this.options.updateWhenIdle ? "moveend" : "move", this._update, this);
          },
          _addScales: function(options, className, container) {
            if (options.metric) {
              this._mScale = create$1("div", className, container);
            }
            if (options.imperial) {
              this._iScale = create$1("div", className, container);
            }
          },
          _update: function() {
            var map2 = this._map, y = map2.getSize().y / 2;
            var maxMeters = map2.distance(
              map2.containerPointToLatLng([0, y]),
              map2.containerPointToLatLng([this.options.maxWidth, y])
            );
            this._updateScales(maxMeters);
          },
          _updateScales: function(maxMeters) {
            if (this.options.metric && maxMeters) {
              this._updateMetric(maxMeters);
            }
            if (this.options.imperial && maxMeters) {
              this._updateImperial(maxMeters);
            }
          },
          _updateMetric: function(maxMeters) {
            var meters = this._getRoundNum(maxMeters), label = meters < 1e3 ? meters + " m" : meters / 1e3 + " km";
            this._updateScale(this._mScale, label, meters / maxMeters);
          },
          _updateImperial: function(maxMeters) {
            var maxFeet = maxMeters * 3.2808399, maxMiles, miles, feet;
            if (maxFeet > 5280) {
              maxMiles = maxFeet / 5280;
              miles = this._getRoundNum(maxMiles);
              this._updateScale(this._iScale, miles + " mi", miles / maxMiles);
            } else {
              feet = this._getRoundNum(maxFeet);
              this._updateScale(this._iScale, feet + " ft", feet / maxFeet);
            }
          },
          _updateScale: function(scale2, text, ratio) {
            scale2.style.width = Math.round(this.options.maxWidth * ratio) + "px";
            scale2.innerHTML = text;
          },
          _getRoundNum: function(num) {
            var pow10 = Math.pow(10, (Math.floor(num) + "").length - 1), d = num / pow10;
            d = d >= 10 ? 10 : d >= 5 ? 5 : d >= 3 ? 3 : d >= 2 ? 2 : 1;
            return pow10 * d;
          }
        });
        var scale = function(options) {
          return new Scale(options);
        };
        var ukrainianFlag = '<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="12" height="8" viewBox="0 0 12 8" class="leaflet-attribution-flag"><path fill="#4C7BE1" d="M0 0h12v4H0z"/><path fill="#FFD500" d="M0 4h12v3H0z"/><path fill="#E0BC00" d="M0 7h12v1H0z"/></svg>';
        var Attribution = Control.extend({
          // @section
          // @aka Control.Attribution options
          options: {
            position: "bottomright",
            // @option prefix: String|false = 'Leaflet'
            // The HTML text shown before the attributions. Pass `false` to disable.
            prefix: '<a href="https://leafletjs.com" title="A JavaScript library for interactive maps">' + (Browser.inlineSvg ? ukrainianFlag + " " : "") + "Leaflet</a>"
          },
          initialize: function(options) {
            setOptions(this, options);
            this._attributions = {};
          },
          onAdd: function(map2) {
            map2.attributionControl = this;
            this._container = create$1("div", "leaflet-control-attribution");
            disableClickPropagation(this._container);
            for (var i in map2._layers) {
              if (map2._layers[i].getAttribution) {
                this.addAttribution(map2._layers[i].getAttribution());
              }
            }
            this._update();
            map2.on("layeradd", this._addAttribution, this);
            return this._container;
          },
          onRemove: function(map2) {
            map2.off("layeradd", this._addAttribution, this);
          },
          _addAttribution: function(ev) {
            if (ev.layer.getAttribution) {
              this.addAttribution(ev.layer.getAttribution());
              ev.layer.once("remove", function() {
                this.removeAttribution(ev.layer.getAttribution());
              }, this);
            }
          },
          // @method setPrefix(prefix: String|false): this
          // The HTML text shown before the attributions. Pass `false` to disable.
          setPrefix: function(prefix) {
            this.options.prefix = prefix;
            this._update();
            return this;
          },
          // @method addAttribution(text: String): this
          // Adds an attribution text (e.g. `'&copy; OpenStreetMap contributors'`).
          addAttribution: function(text) {
            if (!text) {
              return this;
            }
            if (!this._attributions[text]) {
              this._attributions[text] = 0;
            }
            this._attributions[text]++;
            this._update();
            return this;
          },
          // @method removeAttribution(text: String): this
          // Removes an attribution text.
          removeAttribution: function(text) {
            if (!text) {
              return this;
            }
            if (this._attributions[text]) {
              this._attributions[text]--;
              this._update();
            }
            return this;
          },
          _update: function() {
            if (!this._map) {
              return;
            }
            var attribs = [];
            for (var i in this._attributions) {
              if (this._attributions[i]) {
                attribs.push(i);
              }
            }
            var prefixAndAttribs = [];
            if (this.options.prefix) {
              prefixAndAttribs.push(this.options.prefix);
            }
            if (attribs.length) {
              prefixAndAttribs.push(attribs.join(", "));
            }
            this._container.innerHTML = prefixAndAttribs.join(' <span aria-hidden="true">|</span> ');
          }
        });
        Map3.mergeOptions({
          attributionControl: true
        });
        Map3.addInitHook(function() {
          if (this.options.attributionControl) {
            new Attribution().addTo(this);
          }
        });
        var attribution = function(options) {
          return new Attribution(options);
        };
        Control.Layers = Layers;
        Control.Zoom = Zoom;
        Control.Scale = Scale;
        Control.Attribution = Attribution;
        control.layers = layers;
        control.zoom = zoom;
        control.scale = scale;
        control.attribution = attribution;
        var Handler = Class.extend({
          initialize: function(map2) {
            this._map = map2;
          },
          // @method enable(): this
          // Enables the handler
          enable: function() {
            if (this._enabled) {
              return this;
            }
            this._enabled = true;
            this.addHooks();
            return this;
          },
          // @method disable(): this
          // Disables the handler
          disable: function() {
            if (!this._enabled) {
              return this;
            }
            this._enabled = false;
            this.removeHooks();
            return this;
          },
          // @method enabled(): Boolean
          // Returns `true` if the handler is enabled
          enabled: function() {
            return !!this._enabled;
          }
          // @section Extension methods
          // Classes inheriting from `Handler` must implement the two following methods:
          // @method addHooks()
          // Called when the handler is enabled, should add event hooks.
          // @method removeHooks()
          // Called when the handler is disabled, should remove the event hooks added previously.
        });
        Handler.addTo = function(map2, name) {
          map2.addHandler(name, this);
          return this;
        };
        var Mixin = { Events };
        var START = Browser.touch ? "touchstart mousedown" : "mousedown";
        var Draggable = Evented.extend({
          options: {
            // @section
            // @aka Draggable options
            // @option clickTolerance: Number = 3
            // The max number of pixels a user can shift the mouse pointer during a click
            // for it to be considered a valid click (as opposed to a mouse drag).
            clickTolerance: 3
          },
          // @constructor L.Draggable(el: HTMLElement, dragHandle?: HTMLElement, preventOutline?: Boolean, options?: Draggable options)
          // Creates a `Draggable` object for moving `el` when you start dragging the `dragHandle` element (equals `el` itself by default).
          initialize: function(element, dragStartTarget, preventOutline2, options) {
            setOptions(this, options);
            this._element = element;
            this._dragStartTarget = dragStartTarget || element;
            this._preventOutline = preventOutline2;
          },
          // @method enable()
          // Enables the dragging ability
          enable: function() {
            if (this._enabled) {
              return;
            }
            on(this._dragStartTarget, START, this._onDown, this);
            this._enabled = true;
          },
          // @method disable()
          // Disables the dragging ability
          disable: function() {
            if (!this._enabled) {
              return;
            }
            if (Draggable._dragging === this) {
              this.finishDrag(true);
            }
            off(this._dragStartTarget, START, this._onDown, this);
            this._enabled = false;
            this._moved = false;
          },
          _onDown: function(e) {
            if (!this._enabled) {
              return;
            }
            this._moved = false;
            if (hasClass(this._element, "leaflet-zoom-anim")) {
              return;
            }
            if (e.touches && e.touches.length !== 1) {
              if (Draggable._dragging === this) {
                this.finishDrag();
              }
              return;
            }
            if (Draggable._dragging || e.shiftKey || e.which !== 1 && e.button !== 1 && !e.touches) {
              return;
            }
            Draggable._dragging = this;
            if (this._preventOutline) {
              preventOutline(this._element);
            }
            disableImageDrag();
            disableTextSelection();
            if (this._moving) {
              return;
            }
            this.fire("down");
            var first = e.touches ? e.touches[0] : e, sizedParent = getSizedParentNode(this._element);
            this._startPoint = new Point(first.clientX, first.clientY);
            this._startPos = getPosition(this._element);
            this._parentScale = getScale(sizedParent);
            var mouseevent = e.type === "mousedown";
            on(document, mouseevent ? "mousemove" : "touchmove", this._onMove, this);
            on(document, mouseevent ? "mouseup" : "touchend touchcancel", this._onUp, this);
          },
          _onMove: function(e) {
            if (!this._enabled) {
              return;
            }
            if (e.touches && e.touches.length > 1) {
              this._moved = true;
              return;
            }
            var first = e.touches && e.touches.length === 1 ? e.touches[0] : e, offset = new Point(first.clientX, first.clientY)._subtract(this._startPoint);
            if (!offset.x && !offset.y) {
              return;
            }
            if (Math.abs(offset.x) + Math.abs(offset.y) < this.options.clickTolerance) {
              return;
            }
            offset.x /= this._parentScale.x;
            offset.y /= this._parentScale.y;
            preventDefault(e);
            if (!this._moved) {
              this.fire("dragstart");
              this._moved = true;
              addClass(document.body, "leaflet-dragging");
              this._lastTarget = e.target || e.srcElement;
              if (window.SVGElementInstance && this._lastTarget instanceof window.SVGElementInstance) {
                this._lastTarget = this._lastTarget.correspondingUseElement;
              }
              addClass(this._lastTarget, "leaflet-drag-target");
            }
            this._newPos = this._startPos.add(offset);
            this._moving = true;
            this._lastEvent = e;
            this._updatePosition();
          },
          _updatePosition: function() {
            var e = { originalEvent: this._lastEvent };
            this.fire("predrag", e);
            setPosition(this._element, this._newPos);
            this.fire("drag", e);
          },
          _onUp: function() {
            if (!this._enabled) {
              return;
            }
            this.finishDrag();
          },
          finishDrag: function(noInertia) {
            removeClass(document.body, "leaflet-dragging");
            if (this._lastTarget) {
              removeClass(this._lastTarget, "leaflet-drag-target");
              this._lastTarget = null;
            }
            off(document, "mousemove touchmove", this._onMove, this);
            off(document, "mouseup touchend touchcancel", this._onUp, this);
            enableImageDrag();
            enableTextSelection();
            var fireDragend = this._moved && this._moving;
            this._moving = false;
            Draggable._dragging = false;
            if (fireDragend) {
              this.fire("dragend", {
                noInertia,
                distance: this._newPos.distanceTo(this._startPos)
              });
            }
          }
        });
        function clipPolygon(points, bounds, round) {
          var clippedPoints, edges = [1, 4, 2, 8], i, j, k, a, b, len, edge2, p;
          for (i = 0, len = points.length; i < len; i++) {
            points[i]._code = _getBitCode(points[i], bounds);
          }
          for (k = 0; k < 4; k++) {
            edge2 = edges[k];
            clippedPoints = [];
            for (i = 0, len = points.length, j = len - 1; i < len; j = i++) {
              a = points[i];
              b = points[j];
              if (!(a._code & edge2)) {
                if (b._code & edge2) {
                  p = _getEdgeIntersection(b, a, edge2, bounds, round);
                  p._code = _getBitCode(p, bounds);
                  clippedPoints.push(p);
                }
                clippedPoints.push(a);
              } else if (!(b._code & edge2)) {
                p = _getEdgeIntersection(b, a, edge2, bounds, round);
                p._code = _getBitCode(p, bounds);
                clippedPoints.push(p);
              }
            }
            points = clippedPoints;
          }
          return points;
        }
        function polygonCenter(latlngs, crs) {
          var i, j, p1, p2, f, area, x, y, center;
          if (!latlngs || latlngs.length === 0) {
            throw new Error("latlngs not passed");
          }
          if (!isFlat(latlngs)) {
            console.warn("latlngs are not flat! Only the first ring will be used");
            latlngs = latlngs[0];
          }
          var centroidLatLng = toLatLng([0, 0]);
          var bounds = toLatLngBounds(latlngs);
          var areaBounds = bounds.getNorthWest().distanceTo(bounds.getSouthWest()) * bounds.getNorthEast().distanceTo(bounds.getNorthWest());
          if (areaBounds < 1700) {
            centroidLatLng = centroid(latlngs);
          }
          var len = latlngs.length;
          var points = [];
          for (i = 0; i < len; i++) {
            var latlng = toLatLng(latlngs[i]);
            points.push(crs.project(toLatLng([latlng.lat - centroidLatLng.lat, latlng.lng - centroidLatLng.lng])));
          }
          area = x = y = 0;
          for (i = 0, j = len - 1; i < len; j = i++) {
            p1 = points[i];
            p2 = points[j];
            f = p1.y * p2.x - p2.y * p1.x;
            x += (p1.x + p2.x) * f;
            y += (p1.y + p2.y) * f;
            area += f * 3;
          }
          if (area === 0) {
            center = points[0];
          } else {
            center = [x / area, y / area];
          }
          var latlngCenter = crs.unproject(toPoint(center));
          return toLatLng([latlngCenter.lat + centroidLatLng.lat, latlngCenter.lng + centroidLatLng.lng]);
        }
        function centroid(coords) {
          var latSum = 0;
          var lngSum = 0;
          var len = 0;
          for (var i = 0; i < coords.length; i++) {
            var latlng = toLatLng(coords[i]);
            latSum += latlng.lat;
            lngSum += latlng.lng;
            len++;
          }
          return toLatLng([latSum / len, lngSum / len]);
        }
        var PolyUtil = {
          __proto__: null,
          clipPolygon,
          polygonCenter,
          centroid
        };
        function simplify(points, tolerance) {
          if (!tolerance || !points.length) {
            return points.slice();
          }
          var sqTolerance = tolerance * tolerance;
          points = _reducePoints(points, sqTolerance);
          points = _simplifyDP(points, sqTolerance);
          return points;
        }
        function pointToSegmentDistance(p, p1, p2) {
          return Math.sqrt(_sqClosestPointOnSegment(p, p1, p2, true));
        }
        function closestPointOnSegment(p, p1, p2) {
          return _sqClosestPointOnSegment(p, p1, p2);
        }
        function _simplifyDP(points, sqTolerance) {
          var len = points.length, ArrayConstructor = typeof Uint8Array !== "undefined" ? Uint8Array : Array, markers = new ArrayConstructor(len);
          markers[0] = markers[len - 1] = 1;
          _simplifyDPStep(points, markers, sqTolerance, 0, len - 1);
          var i, newPoints = [];
          for (i = 0; i < len; i++) {
            if (markers[i]) {
              newPoints.push(points[i]);
            }
          }
          return newPoints;
        }
        function _simplifyDPStep(points, markers, sqTolerance, first, last) {
          var maxSqDist = 0, index2, i, sqDist;
          for (i = first + 1; i <= last - 1; i++) {
            sqDist = _sqClosestPointOnSegment(points[i], points[first], points[last], true);
            if (sqDist > maxSqDist) {
              index2 = i;
              maxSqDist = sqDist;
            }
          }
          if (maxSqDist > sqTolerance) {
            markers[index2] = 1;
            _simplifyDPStep(points, markers, sqTolerance, first, index2);
            _simplifyDPStep(points, markers, sqTolerance, index2, last);
          }
        }
        function _reducePoints(points, sqTolerance) {
          var reducedPoints = [points[0]];
          for (var i = 1, prev = 0, len = points.length; i < len; i++) {
            if (_sqDist(points[i], points[prev]) > sqTolerance) {
              reducedPoints.push(points[i]);
              prev = i;
            }
          }
          if (prev < len - 1) {
            reducedPoints.push(points[len - 1]);
          }
          return reducedPoints;
        }
        var _lastCode;
        function clipSegment(a, b, bounds, useLastCode, round) {
          var codeA = useLastCode ? _lastCode : _getBitCode(a, bounds), codeB = _getBitCode(b, bounds), codeOut, p, newCode;
          _lastCode = codeB;
          while (true) {
            if (!(codeA | codeB)) {
              return [a, b];
            }
            if (codeA & codeB) {
              return false;
            }
            codeOut = codeA || codeB;
            p = _getEdgeIntersection(a, b, codeOut, bounds, round);
            newCode = _getBitCode(p, bounds);
            if (codeOut === codeA) {
              a = p;
              codeA = newCode;
            } else {
              b = p;
              codeB = newCode;
            }
          }
        }
        function _getEdgeIntersection(a, b, code, bounds, round) {
          var dx = b.x - a.x, dy = b.y - a.y, min = bounds.min, max = bounds.max, x, y;
          if (code & 8) {
            x = a.x + dx * (max.y - a.y) / dy;
            y = max.y;
          } else if (code & 4) {
            x = a.x + dx * (min.y - a.y) / dy;
            y = min.y;
          } else if (code & 2) {
            x = max.x;
            y = a.y + dy * (max.x - a.x) / dx;
          } else if (code & 1) {
            x = min.x;
            y = a.y + dy * (min.x - a.x) / dx;
          }
          return new Point(x, y, round);
        }
        function _getBitCode(p, bounds) {
          var code = 0;
          if (p.x < bounds.min.x) {
            code |= 1;
          } else if (p.x > bounds.max.x) {
            code |= 2;
          }
          if (p.y < bounds.min.y) {
            code |= 4;
          } else if (p.y > bounds.max.y) {
            code |= 8;
          }
          return code;
        }
        function _sqDist(p1, p2) {
          var dx = p2.x - p1.x, dy = p2.y - p1.y;
          return dx * dx + dy * dy;
        }
        function _sqClosestPointOnSegment(p, p1, p2, sqDist) {
          var x = p1.x, y = p1.y, dx = p2.x - x, dy = p2.y - y, dot = dx * dx + dy * dy, t;
          if (dot > 0) {
            t = ((p.x - x) * dx + (p.y - y) * dy) / dot;
            if (t > 1) {
              x = p2.x;
              y = p2.y;
            } else if (t > 0) {
              x += dx * t;
              y += dy * t;
            }
          }
          dx = p.x - x;
          dy = p.y - y;
          return sqDist ? dx * dx + dy * dy : new Point(x, y);
        }
        function isFlat(latlngs) {
          return !isArray(latlngs[0]) || typeof latlngs[0][0] !== "object" && typeof latlngs[0][0] !== "undefined";
        }
        function _flat(latlngs) {
          console.warn("Deprecated use of _flat, please use L.LineUtil.isFlat instead.");
          return isFlat(latlngs);
        }
        function polylineCenter(latlngs, crs) {
          var i, halfDist, segDist, dist, p1, p2, ratio, center;
          if (!latlngs || latlngs.length === 0) {
            throw new Error("latlngs not passed");
          }
          if (!isFlat(latlngs)) {
            console.warn("latlngs are not flat! Only the first ring will be used");
            latlngs = latlngs[0];
          }
          var centroidLatLng = toLatLng([0, 0]);
          var bounds = toLatLngBounds(latlngs);
          var areaBounds = bounds.getNorthWest().distanceTo(bounds.getSouthWest()) * bounds.getNorthEast().distanceTo(bounds.getNorthWest());
          if (areaBounds < 1700) {
            centroidLatLng = centroid(latlngs);
          }
          var len = latlngs.length;
          var points = [];
          for (i = 0; i < len; i++) {
            var latlng = toLatLng(latlngs[i]);
            points.push(crs.project(toLatLng([latlng.lat - centroidLatLng.lat, latlng.lng - centroidLatLng.lng])));
          }
          for (i = 0, halfDist = 0; i < len - 1; i++) {
            halfDist += points[i].distanceTo(points[i + 1]) / 2;
          }
          if (halfDist === 0) {
            center = points[0];
          } else {
            for (i = 0, dist = 0; i < len - 1; i++) {
              p1 = points[i];
              p2 = points[i + 1];
              segDist = p1.distanceTo(p2);
              dist += segDist;
              if (dist > halfDist) {
                ratio = (dist - halfDist) / segDist;
                center = [
                  p2.x - ratio * (p2.x - p1.x),
                  p2.y - ratio * (p2.y - p1.y)
                ];
                break;
              }
            }
          }
          var latlngCenter = crs.unproject(toPoint(center));
          return toLatLng([latlngCenter.lat + centroidLatLng.lat, latlngCenter.lng + centroidLatLng.lng]);
        }
        var LineUtil = {
          __proto__: null,
          simplify,
          pointToSegmentDistance,
          closestPointOnSegment,
          clipSegment,
          _getEdgeIntersection,
          _getBitCode,
          _sqClosestPointOnSegment,
          isFlat,
          _flat,
          polylineCenter
        };
        var LonLat = {
          project: function(latlng) {
            return new Point(latlng.lng, latlng.lat);
          },
          unproject: function(point) {
            return new LatLng(point.y, point.x);
          },
          bounds: new Bounds([-180, -90], [180, 90])
        };
        var Mercator = {
          R: 6378137,
          R_MINOR: 6356752314245179e-9,
          bounds: new Bounds([-2003750834279e-5, -1549657073972e-5], [2003750834279e-5, 1876465623138e-5]),
          project: function(latlng) {
            var d = Math.PI / 180, r = this.R, y = latlng.lat * d, tmp2 = this.R_MINOR / r, e = Math.sqrt(1 - tmp2 * tmp2), con = e * Math.sin(y);
            var ts = Math.tan(Math.PI / 4 - y / 2) / Math.pow((1 - con) / (1 + con), e / 2);
            y = -r * Math.log(Math.max(ts, 1e-10));
            return new Point(latlng.lng * d * r, y);
          },
          unproject: function(point) {
            var d = 180 / Math.PI, r = this.R, tmp2 = this.R_MINOR / r, e = Math.sqrt(1 - tmp2 * tmp2), ts = Math.exp(-point.y / r), phi = Math.PI / 2 - 2 * Math.atan(ts);
            for (var i = 0, dphi = 0.1, con; i < 15 && Math.abs(dphi) > 1e-7; i++) {
              con = e * Math.sin(phi);
              con = Math.pow((1 - con) / (1 + con), e / 2);
              dphi = Math.PI / 2 - 2 * Math.atan(ts * con) - phi;
              phi += dphi;
            }
            return new LatLng(phi * d, point.x * d / r);
          }
        };
        var index = {
          __proto__: null,
          LonLat,
          Mercator,
          SphericalMercator
        };
        var EPSG3395 = extend({}, Earth, {
          code: "EPSG:3395",
          projection: Mercator,
          transformation: function() {
            var scale2 = 0.5 / (Math.PI * Mercator.R);
            return toTransformation(scale2, 0.5, -scale2, 0.5);
          }()
        });
        var EPSG4326 = extend({}, Earth, {
          code: "EPSG:4326",
          projection: LonLat,
          transformation: toTransformation(1 / 180, 1, -1 / 180, 0.5)
        });
        var Simple = extend({}, CRS, {
          projection: LonLat,
          transformation: toTransformation(1, 0, -1, 0),
          scale: function(zoom2) {
            return Math.pow(2, zoom2);
          },
          zoom: function(scale2) {
            return Math.log(scale2) / Math.LN2;
          },
          distance: function(latlng1, latlng2) {
            var dx = latlng2.lng - latlng1.lng, dy = latlng2.lat - latlng1.lat;
            return Math.sqrt(dx * dx + dy * dy);
          },
          infinite: true
        });
        CRS.Earth = Earth;
        CRS.EPSG3395 = EPSG3395;
        CRS.EPSG3857 = EPSG3857;
        CRS.EPSG900913 = EPSG900913;
        CRS.EPSG4326 = EPSG4326;
        CRS.Simple = Simple;
        var Layer = Evented.extend({
          // Classes extending `L.Layer` will inherit the following options:
          options: {
            // @option pane: String = 'overlayPane'
            // By default the layer will be added to the map's [overlay pane](#map-overlaypane). Overriding this option will cause the layer to be placed on another pane by default.
            pane: "overlayPane",
            // @option attribution: String = null
            // String to be shown in the attribution control, e.g. "© OpenStreetMap contributors". It describes the layer data and is often a legal obligation towards copyright holders and tile providers.
            attribution: null,
            bubblingMouseEvents: true
          },
          /* @section
           * Classes extending `L.Layer` will inherit the following methods:
           *
           * @method addTo(map: Map|LayerGroup): this
           * Adds the layer to the given map or layer group.
           */
          addTo: function(map2) {
            map2.addLayer(this);
            return this;
          },
          // @method remove: this
          // Removes the layer from the map it is currently active on.
          remove: function() {
            return this.removeFrom(this._map || this._mapToAdd);
          },
          // @method removeFrom(map: Map): this
          // Removes the layer from the given map
          //
          // @alternative
          // @method removeFrom(group: LayerGroup): this
          // Removes the layer from the given `LayerGroup`
          removeFrom: function(obj) {
            if (obj) {
              obj.removeLayer(this);
            }
            return this;
          },
          // @method getPane(name? : String): HTMLElement
          // Returns the `HTMLElement` representing the named pane on the map. If `name` is omitted, returns the pane for this layer.
          getPane: function(name) {
            return this._map.getPane(name ? this.options[name] || name : this.options.pane);
          },
          addInteractiveTarget: function(targetEl) {
            this._map._targets[stamp(targetEl)] = this;
            return this;
          },
          removeInteractiveTarget: function(targetEl) {
            delete this._map._targets[stamp(targetEl)];
            return this;
          },
          // @method getAttribution: String
          // Used by the `attribution control`, returns the [attribution option](#gridlayer-attribution).
          getAttribution: function() {
            return this.options.attribution;
          },
          _layerAdd: function(e) {
            var map2 = e.target;
            if (!map2.hasLayer(this)) {
              return;
            }
            this._map = map2;
            this._zoomAnimated = map2._zoomAnimated;
            if (this.getEvents) {
              var events = this.getEvents();
              map2.on(events, this);
              this.once("remove", function() {
                map2.off(events, this);
              }, this);
            }
            this.onAdd(map2);
            this.fire("add");
            map2.fire("layeradd", { layer: this });
          }
        });
        Map3.include({
          // @method addLayer(layer: Layer): this
          // Adds the given layer to the map
          addLayer: function(layer) {
            if (!layer._layerAdd) {
              throw new Error("The provided object is not a Layer.");
            }
            var id = stamp(layer);
            if (this._layers[id]) {
              return this;
            }
            this._layers[id] = layer;
            layer._mapToAdd = this;
            if (layer.beforeAdd) {
              layer.beforeAdd(this);
            }
            this.whenReady(layer._layerAdd, layer);
            return this;
          },
          // @method removeLayer(layer: Layer): this
          // Removes the given layer from the map.
          removeLayer: function(layer) {
            var id = stamp(layer);
            if (!this._layers[id]) {
              return this;
            }
            if (this._loaded) {
              layer.onRemove(this);
            }
            delete this._layers[id];
            if (this._loaded) {
              this.fire("layerremove", { layer });
              layer.fire("remove");
            }
            layer._map = layer._mapToAdd = null;
            return this;
          },
          // @method hasLayer(layer: Layer): Boolean
          // Returns `true` if the given layer is currently added to the map
          hasLayer: function(layer) {
            return stamp(layer) in this._layers;
          },
          /* @method eachLayer(fn: Function, context?: Object): this
           * Iterates over the layers of the map, optionally specifying context of the iterator function.
           * ```
           * map.eachLayer(function(layer){
           *     layer.bindPopup('Hello');
           * });
           * ```
           */
          eachLayer: function(method, context) {
            for (var i in this._layers) {
              method.call(context, this._layers[i]);
            }
            return this;
          },
          _addLayers: function(layers2) {
            layers2 = layers2 ? isArray(layers2) ? layers2 : [layers2] : [];
            for (var i = 0, len = layers2.length; i < len; i++) {
              this.addLayer(layers2[i]);
            }
          },
          _addZoomLimit: function(layer) {
            if (!isNaN(layer.options.maxZoom) || !isNaN(layer.options.minZoom)) {
              this._zoomBoundLayers[stamp(layer)] = layer;
              this._updateZoomLevels();
            }
          },
          _removeZoomLimit: function(layer) {
            var id = stamp(layer);
            if (this._zoomBoundLayers[id]) {
              delete this._zoomBoundLayers[id];
              this._updateZoomLevels();
            }
          },
          _updateZoomLevels: function() {
            var minZoom = Infinity, maxZoom = -Infinity, oldZoomSpan = this._getZoomSpan();
            for (var i in this._zoomBoundLayers) {
              var options = this._zoomBoundLayers[i].options;
              minZoom = options.minZoom === void 0 ? minZoom : Math.min(minZoom, options.minZoom);
              maxZoom = options.maxZoom === void 0 ? maxZoom : Math.max(maxZoom, options.maxZoom);
            }
            this._layersMaxZoom = maxZoom === -Infinity ? void 0 : maxZoom;
            this._layersMinZoom = minZoom === Infinity ? void 0 : minZoom;
            if (oldZoomSpan !== this._getZoomSpan()) {
              this.fire("zoomlevelschange");
            }
            if (this.options.maxZoom === void 0 && this._layersMaxZoom && this.getZoom() > this._layersMaxZoom) {
              this.setZoom(this._layersMaxZoom);
            }
            if (this.options.minZoom === void 0 && this._layersMinZoom && this.getZoom() < this._layersMinZoom) {
              this.setZoom(this._layersMinZoom);
            }
          }
        });
        var LayerGroup = Layer.extend({
          initialize: function(layers2, options) {
            setOptions(this, options);
            this._layers = {};
            var i, len;
            if (layers2) {
              for (i = 0, len = layers2.length; i < len; i++) {
                this.addLayer(layers2[i]);
              }
            }
          },
          // @method addLayer(layer: Layer): this
          // Adds the given layer to the group.
          addLayer: function(layer) {
            var id = this.getLayerId(layer);
            this._layers[id] = layer;
            if (this._map) {
              this._map.addLayer(layer);
            }
            return this;
          },
          // @method removeLayer(layer: Layer): this
          // Removes the given layer from the group.
          // @alternative
          // @method removeLayer(id: Number): this
          // Removes the layer with the given internal ID from the group.
          removeLayer: function(layer) {
            var id = layer in this._layers ? layer : this.getLayerId(layer);
            if (this._map && this._layers[id]) {
              this._map.removeLayer(this._layers[id]);
            }
            delete this._layers[id];
            return this;
          },
          // @method hasLayer(layer: Layer): Boolean
          // Returns `true` if the given layer is currently added to the group.
          // @alternative
          // @method hasLayer(id: Number): Boolean
          // Returns `true` if the given internal ID is currently added to the group.
          hasLayer: function(layer) {
            var layerId = typeof layer === "number" ? layer : this.getLayerId(layer);
            return layerId in this._layers;
          },
          // @method clearLayers(): this
          // Removes all the layers from the group.
          clearLayers: function() {
            return this.eachLayer(this.removeLayer, this);
          },
          // @method invoke(methodName: String, …): this
          // Calls `methodName` on every layer contained in this group, passing any
          // additional parameters. Has no effect if the layers contained do not
          // implement `methodName`.
          invoke: function(methodName) {
            var args = Array.prototype.slice.call(arguments, 1), i, layer;
            for (i in this._layers) {
              layer = this._layers[i];
              if (layer[methodName]) {
                layer[methodName].apply(layer, args);
              }
            }
            return this;
          },
          onAdd: function(map2) {
            this.eachLayer(map2.addLayer, map2);
          },
          onRemove: function(map2) {
            this.eachLayer(map2.removeLayer, map2);
          },
          // @method eachLayer(fn: Function, context?: Object): this
          // Iterates over the layers of the group, optionally specifying context of the iterator function.
          // ```js
          // group.eachLayer(function (layer) {
          // 	layer.bindPopup('Hello');
          // });
          // ```
          eachLayer: function(method, context) {
            for (var i in this._layers) {
              method.call(context, this._layers[i]);
            }
            return this;
          },
          // @method getLayer(id: Number): Layer
          // Returns the layer with the given internal ID.
          getLayer: function(id) {
            return this._layers[id];
          },
          // @method getLayers(): Layer[]
          // Returns an array of all the layers added to the group.
          getLayers: function() {
            var layers2 = [];
            this.eachLayer(layers2.push, layers2);
            return layers2;
          },
          // @method setZIndex(zIndex: Number): this
          // Calls `setZIndex` on every layer contained in this group, passing the z-index.
          setZIndex: function(zIndex) {
            return this.invoke("setZIndex", zIndex);
          },
          // @method getLayerId(layer: Layer): Number
          // Returns the internal ID for a layer
          getLayerId: function(layer) {
            return stamp(layer);
          }
        });
        var layerGroup = function(layers2, options) {
          return new LayerGroup(layers2, options);
        };
        var FeatureGroup = LayerGroup.extend({
          addLayer: function(layer) {
            if (this.hasLayer(layer)) {
              return this;
            }
            layer.addEventParent(this);
            LayerGroup.prototype.addLayer.call(this, layer);
            return this.fire("layeradd", { layer });
          },
          removeLayer: function(layer) {
            if (!this.hasLayer(layer)) {
              return this;
            }
            if (layer in this._layers) {
              layer = this._layers[layer];
            }
            layer.removeEventParent(this);
            LayerGroup.prototype.removeLayer.call(this, layer);
            return this.fire("layerremove", { layer });
          },
          // @method setStyle(style: Path options): this
          // Sets the given path options to each layer of the group that has a `setStyle` method.
          setStyle: function(style2) {
            return this.invoke("setStyle", style2);
          },
          // @method bringToFront(): this
          // Brings the layer group to the top of all other layers
          bringToFront: function() {
            return this.invoke("bringToFront");
          },
          // @method bringToBack(): this
          // Brings the layer group to the back of all other layers
          bringToBack: function() {
            return this.invoke("bringToBack");
          },
          // @method getBounds(): LatLngBounds
          // Returns the LatLngBounds of the Feature Group (created from bounds and coordinates of its children).
          getBounds: function() {
            var bounds = new LatLngBounds();
            for (var id in this._layers) {
              var layer = this._layers[id];
              bounds.extend(layer.getBounds ? layer.getBounds() : layer.getLatLng());
            }
            return bounds;
          }
        });
        var featureGroup = function(layers2, options) {
          return new FeatureGroup(layers2, options);
        };
        var Icon = Class.extend({
          /* @section
           * @aka Icon options
           *
           * @option iconUrl: String = null
           * **(required)** The URL to the icon image (absolute or relative to your script path).
           *
           * @option iconRetinaUrl: String = null
           * The URL to a retina sized version of the icon image (absolute or relative to your
           * script path). Used for Retina screen devices.
           *
           * @option iconSize: Point = null
           * Size of the icon image in pixels.
           *
           * @option iconAnchor: Point = null
           * The coordinates of the "tip" of the icon (relative to its top left corner). The icon
           * will be aligned so that this point is at the marker's geographical location. Centered
           * by default if size is specified, also can be set in CSS with negative margins.
           *
           * @option popupAnchor: Point = [0, 0]
           * The coordinates of the point from which popups will "open", relative to the icon anchor.
           *
           * @option tooltipAnchor: Point = [0, 0]
           * The coordinates of the point from which tooltips will "open", relative to the icon anchor.
           *
           * @option shadowUrl: String = null
           * The URL to the icon shadow image. If not specified, no shadow image will be created.
           *
           * @option shadowRetinaUrl: String = null
           *
           * @option shadowSize: Point = null
           * Size of the shadow image in pixels.
           *
           * @option shadowAnchor: Point = null
           * The coordinates of the "tip" of the shadow (relative to its top left corner) (the same
           * as iconAnchor if not specified).
           *
           * @option className: String = ''
           * A custom class name to assign to both icon and shadow images. Empty by default.
           */
          options: {
            popupAnchor: [0, 0],
            tooltipAnchor: [0, 0],
            // @option crossOrigin: Boolean|String = false
            // Whether the crossOrigin attribute will be added to the tiles.
            // If a String is provided, all tiles will have their crossOrigin attribute set to the String provided. This is needed if you want to access tile pixel data.
            // Refer to [CORS Settings](https://developer.mozilla.org/en-US/docs/Web/HTML/CORS_settings_attributes) for valid String values.
            crossOrigin: false
          },
          initialize: function(options) {
            setOptions(this, options);
          },
          // @method createIcon(oldIcon?: HTMLElement): HTMLElement
          // Called internally when the icon has to be shown, returns a `<img>` HTML element
          // styled according to the options.
          createIcon: function(oldIcon) {
            return this._createIcon("icon", oldIcon);
          },
          // @method createShadow(oldIcon?: HTMLElement): HTMLElement
          // As `createIcon`, but for the shadow beneath it.
          createShadow: function(oldIcon) {
            return this._createIcon("shadow", oldIcon);
          },
          _createIcon: function(name, oldIcon) {
            var src = this._getIconUrl(name);
            if (!src) {
              if (name === "icon") {
                throw new Error("iconUrl not set in Icon options (see the docs).");
              }
              return null;
            }
            var img = this._createImg(src, oldIcon && oldIcon.tagName === "IMG" ? oldIcon : null);
            this._setIconStyles(img, name);
            if (this.options.crossOrigin || this.options.crossOrigin === "") {
              img.crossOrigin = this.options.crossOrigin === true ? "" : this.options.crossOrigin;
            }
            return img;
          },
          _setIconStyles: function(img, name) {
            var options = this.options;
            var sizeOption = options[name + "Size"];
            if (typeof sizeOption === "number") {
              sizeOption = [sizeOption, sizeOption];
            }
            var size = toPoint(sizeOption), anchor = toPoint(name === "shadow" && options.shadowAnchor || options.iconAnchor || size && size.divideBy(2, true));
            img.className = "leaflet-marker-" + name + " " + (options.className || "");
            if (anchor) {
              img.style.marginLeft = -anchor.x + "px";
              img.style.marginTop = -anchor.y + "px";
            }
            if (size) {
              img.style.width = size.x + "px";
              img.style.height = size.y + "px";
            }
          },
          _createImg: function(src, el) {
            el = el || document.createElement("img");
            el.src = src;
            return el;
          },
          _getIconUrl: function(name) {
            return Browser.retina && this.options[name + "RetinaUrl"] || this.options[name + "Url"];
          }
        });
        function icon(options) {
          return new Icon(options);
        }
        var IconDefault = Icon.extend({
          options: {
            iconUrl: "marker-icon.png",
            iconRetinaUrl: "marker-icon-2x.png",
            shadowUrl: "marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            tooltipAnchor: [16, -28],
            shadowSize: [41, 41]
          },
          _getIconUrl: function(name) {
            if (typeof IconDefault.imagePath !== "string") {
              IconDefault.imagePath = this._detectIconPath();
            }
            return (this.options.imagePath || IconDefault.imagePath) + Icon.prototype._getIconUrl.call(this, name);
          },
          _stripUrl: function(path) {
            var strip = function(str, re, idx) {
              var match = re.exec(str);
              return match && match[idx];
            };
            path = strip(path, /^url\((['"])?(.+)\1\)$/, 2);
            return path && strip(path, /^(.*)marker-icon\.png$/, 1);
          },
          _detectIconPath: function() {
            var el = create$1("div", "leaflet-default-icon-path", document.body);
            var path = getStyle(el, "background-image") || getStyle(el, "backgroundImage");
            document.body.removeChild(el);
            path = this._stripUrl(path);
            if (path) {
              return path;
            }
            var link = document.querySelector('link[href$="leaflet.css"]');
            if (!link) {
              return "";
            }
            return link.href.substring(0, link.href.length - "leaflet.css".length - 1);
          }
        });
        var MarkerDrag = Handler.extend({
          initialize: function(marker2) {
            this._marker = marker2;
          },
          addHooks: function() {
            var icon2 = this._marker._icon;
            if (!this._draggable) {
              this._draggable = new Draggable(icon2, icon2, true);
            }
            this._draggable.on({
              dragstart: this._onDragStart,
              predrag: this._onPreDrag,
              drag: this._onDrag,
              dragend: this._onDragEnd
            }, this).enable();
            addClass(icon2, "leaflet-marker-draggable");
          },
          removeHooks: function() {
            this._draggable.off({
              dragstart: this._onDragStart,
              predrag: this._onPreDrag,
              drag: this._onDrag,
              dragend: this._onDragEnd
            }, this).disable();
            if (this._marker._icon) {
              removeClass(this._marker._icon, "leaflet-marker-draggable");
            }
          },
          moved: function() {
            return this._draggable && this._draggable._moved;
          },
          _adjustPan: function(e) {
            var marker2 = this._marker, map2 = marker2._map, speed = this._marker.options.autoPanSpeed, padding = this._marker.options.autoPanPadding, iconPos = getPosition(marker2._icon), bounds = map2.getPixelBounds(), origin = map2.getPixelOrigin();
            var panBounds = toBounds(
              bounds.min._subtract(origin).add(padding),
              bounds.max._subtract(origin).subtract(padding)
            );
            if (!panBounds.contains(iconPos)) {
              var movement = toPoint(
                (Math.max(panBounds.max.x, iconPos.x) - panBounds.max.x) / (bounds.max.x - panBounds.max.x) - (Math.min(panBounds.min.x, iconPos.x) - panBounds.min.x) / (bounds.min.x - panBounds.min.x),
                (Math.max(panBounds.max.y, iconPos.y) - panBounds.max.y) / (bounds.max.y - panBounds.max.y) - (Math.min(panBounds.min.y, iconPos.y) - panBounds.min.y) / (bounds.min.y - panBounds.min.y)
              ).multiplyBy(speed);
              map2.panBy(movement, { animate: false });
              this._draggable._newPos._add(movement);
              this._draggable._startPos._add(movement);
              setPosition(marker2._icon, this._draggable._newPos);
              this._onDrag(e);
              this._panRequest = requestAnimFrame(this._adjustPan.bind(this, e));
            }
          },
          _onDragStart: function() {
            this._oldLatLng = this._marker.getLatLng();
            this._marker.closePopup && this._marker.closePopup();
            this._marker.fire("movestart").fire("dragstart");
          },
          _onPreDrag: function(e) {
            if (this._marker.options.autoPan) {
              cancelAnimFrame(this._panRequest);
              this._panRequest = requestAnimFrame(this._adjustPan.bind(this, e));
            }
          },
          _onDrag: function(e) {
            var marker2 = this._marker, shadow = marker2._shadow, iconPos = getPosition(marker2._icon), latlng = marker2._map.layerPointToLatLng(iconPos);
            if (shadow) {
              setPosition(shadow, iconPos);
            }
            marker2._latlng = latlng;
            e.latlng = latlng;
            e.oldLatLng = this._oldLatLng;
            marker2.fire("move", e).fire("drag", e);
          },
          _onDragEnd: function(e) {
            cancelAnimFrame(this._panRequest);
            delete this._oldLatLng;
            this._marker.fire("moveend").fire("dragend", e);
          }
        });
        var Marker = Layer.extend({
          // @section
          // @aka Marker options
          options: {
            // @option icon: Icon = *
            // Icon instance to use for rendering the marker.
            // See [Icon documentation](#L.Icon) for details on how to customize the marker icon.
            // If not specified, a common instance of `L.Icon.Default` is used.
            icon: new IconDefault(),
            // Option inherited from "Interactive layer" abstract class
            interactive: true,
            // @option keyboard: Boolean = true
            // Whether the marker can be tabbed to with a keyboard and clicked by pressing enter.
            keyboard: true,
            // @option title: String = ''
            // Text for the browser tooltip that appear on marker hover (no tooltip by default).
            // [Useful for accessibility](https://leafletjs.com/examples/accessibility/#markers-must-be-labelled).
            title: "",
            // @option alt: String = 'Marker'
            // Text for the `alt` attribute of the icon image.
            // [Useful for accessibility](https://leafletjs.com/examples/accessibility/#markers-must-be-labelled).
            alt: "Marker",
            // @option zIndexOffset: Number = 0
            // By default, marker images zIndex is set automatically based on its latitude. Use this option if you want to put the marker on top of all others (or below), specifying a high value like `1000` (or high negative value, respectively).
            zIndexOffset: 0,
            // @option opacity: Number = 1.0
            // The opacity of the marker.
            opacity: 1,
            // @option riseOnHover: Boolean = false
            // If `true`, the marker will get on top of others when you hover the mouse over it.
            riseOnHover: false,
            // @option riseOffset: Number = 250
            // The z-index offset used for the `riseOnHover` feature.
            riseOffset: 250,
            // @option pane: String = 'markerPane'
            // `Map pane` where the markers icon will be added.
            pane: "markerPane",
            // @option shadowPane: String = 'shadowPane'
            // `Map pane` where the markers shadow will be added.
            shadowPane: "shadowPane",
            // @option bubblingMouseEvents: Boolean = false
            // When `true`, a mouse event on this marker will trigger the same event on the map
            // (unless [`L.DomEvent.stopPropagation`](#domevent-stoppropagation) is used).
            bubblingMouseEvents: false,
            // @option autoPanOnFocus: Boolean = true
            // When `true`, the map will pan whenever the marker is focused (via
            // e.g. pressing `tab` on the keyboard) to ensure the marker is
            // visible within the map's bounds
            autoPanOnFocus: true,
            // @section Draggable marker options
            // @option draggable: Boolean = false
            // Whether the marker is draggable with mouse/touch or not.
            draggable: false,
            // @option autoPan: Boolean = false
            // Whether to pan the map when dragging this marker near its edge or not.
            autoPan: false,
            // @option autoPanPadding: Point = Point(50, 50)
            // Distance (in pixels to the left/right and to the top/bottom) of the
            // map edge to start panning the map.
            autoPanPadding: [50, 50],
            // @option autoPanSpeed: Number = 10
            // Number of pixels the map should pan by.
            autoPanSpeed: 10
          },
          /* @section
           *
           * In addition to [shared layer methods](#Layer) like `addTo()` and `remove()` and [popup methods](#Popup) like bindPopup() you can also use the following methods:
           */
          initialize: function(latlng, options) {
            setOptions(this, options);
            this._latlng = toLatLng(latlng);
          },
          onAdd: function(map2) {
            this._zoomAnimated = this._zoomAnimated && map2.options.markerZoomAnimation;
            if (this._zoomAnimated) {
              map2.on("zoomanim", this._animateZoom, this);
            }
            this._initIcon();
            this.update();
          },
          onRemove: function(map2) {
            if (this.dragging && this.dragging.enabled()) {
              this.options.draggable = true;
              this.dragging.removeHooks();
            }
            delete this.dragging;
            if (this._zoomAnimated) {
              map2.off("zoomanim", this._animateZoom, this);
            }
            this._removeIcon();
            this._removeShadow();
          },
          getEvents: function() {
            return {
              zoom: this.update,
              viewreset: this.update
            };
          },
          // @method getLatLng: LatLng
          // Returns the current geographical position of the marker.
          getLatLng: function() {
            return this._latlng;
          },
          // @method setLatLng(latlng: LatLng): this
          // Changes the marker position to the given point.
          setLatLng: function(latlng) {
            var oldLatLng = this._latlng;
            this._latlng = toLatLng(latlng);
            this.update();
            return this.fire("move", { oldLatLng, latlng: this._latlng });
          },
          // @method setZIndexOffset(offset: Number): this
          // Changes the [zIndex offset](#marker-zindexoffset) of the marker.
          setZIndexOffset: function(offset) {
            this.options.zIndexOffset = offset;
            return this.update();
          },
          // @method getIcon: Icon
          // Returns the current icon used by the marker
          getIcon: function() {
            return this.options.icon;
          },
          // @method setIcon(icon: Icon): this
          // Changes the marker icon.
          setIcon: function(icon2) {
            this.options.icon = icon2;
            if (this._map) {
              this._initIcon();
              this.update();
            }
            if (this._popup) {
              this.bindPopup(this._popup, this._popup.options);
            }
            return this;
          },
          getElement: function() {
            return this._icon;
          },
          update: function() {
            if (this._icon && this._map) {
              var pos = this._map.latLngToLayerPoint(this._latlng).round();
              this._setPos(pos);
            }
            return this;
          },
          _initIcon: function() {
            var options = this.options, classToAdd = "leaflet-zoom-" + (this._zoomAnimated ? "animated" : "hide");
            var icon2 = options.icon.createIcon(this._icon), addIcon = false;
            if (icon2 !== this._icon) {
              if (this._icon) {
                this._removeIcon();
              }
              addIcon = true;
              if (options.title) {
                icon2.title = options.title;
              }
              if (icon2.tagName === "IMG") {
                icon2.alt = options.alt || "";
              }
            }
            addClass(icon2, classToAdd);
            if (options.keyboard) {
              icon2.tabIndex = "0";
              icon2.setAttribute("role", "button");
            }
            this._icon = icon2;
            if (options.riseOnHover) {
              this.on({
                mouseover: this._bringToFront,
                mouseout: this._resetZIndex
              });
            }
            if (this.options.autoPanOnFocus) {
              on(icon2, "focus", this._panOnFocus, this);
            }
            var newShadow = options.icon.createShadow(this._shadow), addShadow = false;
            if (newShadow !== this._shadow) {
              this._removeShadow();
              addShadow = true;
            }
            if (newShadow) {
              addClass(newShadow, classToAdd);
              newShadow.alt = "";
            }
            this._shadow = newShadow;
            if (options.opacity < 1) {
              this._updateOpacity();
            }
            if (addIcon) {
              this.getPane().appendChild(this._icon);
            }
            this._initInteraction();
            if (newShadow && addShadow) {
              this.getPane(options.shadowPane).appendChild(this._shadow);
            }
          },
          _removeIcon: function() {
            if (this.options.riseOnHover) {
              this.off({
                mouseover: this._bringToFront,
                mouseout: this._resetZIndex
              });
            }
            if (this.options.autoPanOnFocus) {
              off(this._icon, "focus", this._panOnFocus, this);
            }
            remove(this._icon);
            this.removeInteractiveTarget(this._icon);
            this._icon = null;
          },
          _removeShadow: function() {
            if (this._shadow) {
              remove(this._shadow);
            }
            this._shadow = null;
          },
          _setPos: function(pos) {
            if (this._icon) {
              setPosition(this._icon, pos);
            }
            if (this._shadow) {
              setPosition(this._shadow, pos);
            }
            this._zIndex = pos.y + this.options.zIndexOffset;
            this._resetZIndex();
          },
          _updateZIndex: function(offset) {
            if (this._icon) {
              this._icon.style.zIndex = this._zIndex + offset;
            }
          },
          _animateZoom: function(opt) {
            var pos = this._map._latLngToNewLayerPoint(this._latlng, opt.zoom, opt.center).round();
            this._setPos(pos);
          },
          _initInteraction: function() {
            if (!this.options.interactive) {
              return;
            }
            addClass(this._icon, "leaflet-interactive");
            this.addInteractiveTarget(this._icon);
            if (MarkerDrag) {
              var draggable = this.options.draggable;
              if (this.dragging) {
                draggable = this.dragging.enabled();
                this.dragging.disable();
              }
              this.dragging = new MarkerDrag(this);
              if (draggable) {
                this.dragging.enable();
              }
            }
          },
          // @method setOpacity(opacity: Number): this
          // Changes the opacity of the marker.
          setOpacity: function(opacity) {
            this.options.opacity = opacity;
            if (this._map) {
              this._updateOpacity();
            }
            return this;
          },
          _updateOpacity: function() {
            var opacity = this.options.opacity;
            if (this._icon) {
              setOpacity(this._icon, opacity);
            }
            if (this._shadow) {
              setOpacity(this._shadow, opacity);
            }
          },
          _bringToFront: function() {
            this._updateZIndex(this.options.riseOffset);
          },
          _resetZIndex: function() {
            this._updateZIndex(0);
          },
          _panOnFocus: function() {
            var map2 = this._map;
            if (!map2) {
              return;
            }
            var iconOpts = this.options.icon.options;
            var size = iconOpts.iconSize ? toPoint(iconOpts.iconSize) : toPoint(0, 0);
            var anchor = iconOpts.iconAnchor ? toPoint(iconOpts.iconAnchor) : toPoint(0, 0);
            map2.panInside(this._latlng, {
              paddingTopLeft: anchor,
              paddingBottomRight: size.subtract(anchor)
            });
          },
          _getPopupAnchor: function() {
            return this.options.icon.options.popupAnchor;
          },
          _getTooltipAnchor: function() {
            return this.options.icon.options.tooltipAnchor;
          }
        });
        function marker(latlng, options) {
          return new Marker(latlng, options);
        }
        var Path = Layer.extend({
          // @section
          // @aka Path options
          options: {
            // @option stroke: Boolean = true
            // Whether to draw stroke along the path. Set it to `false` to disable borders on polygons or circles.
            stroke: true,
            // @option color: String = '#3388ff'
            // Stroke color
            color: "#3388ff",
            // @option weight: Number = 3
            // Stroke width in pixels
            weight: 3,
            // @option opacity: Number = 1.0
            // Stroke opacity
            opacity: 1,
            // @option lineCap: String= 'round'
            // A string that defines [shape to be used at the end](https://developer.mozilla.org/docs/Web/SVG/Attribute/stroke-linecap) of the stroke.
            lineCap: "round",
            // @option lineJoin: String = 'round'
            // A string that defines [shape to be used at the corners](https://developer.mozilla.org/docs/Web/SVG/Attribute/stroke-linejoin) of the stroke.
            lineJoin: "round",
            // @option dashArray: String = null
            // A string that defines the stroke [dash pattern](https://developer.mozilla.org/docs/Web/SVG/Attribute/stroke-dasharray). Doesn't work on `Canvas`-powered layers in [some old browsers](https://developer.mozilla.org/docs/Web/API/CanvasRenderingContext2D/setLineDash#Browser_compatibility).
            dashArray: null,
            // @option dashOffset: String = null
            // A string that defines the [distance into the dash pattern to start the dash](https://developer.mozilla.org/docs/Web/SVG/Attribute/stroke-dashoffset). Doesn't work on `Canvas`-powered layers in [some old browsers](https://developer.mozilla.org/docs/Web/API/CanvasRenderingContext2D/setLineDash#Browser_compatibility).
            dashOffset: null,
            // @option fill: Boolean = depends
            // Whether to fill the path with color. Set it to `false` to disable filling on polygons or circles.
            fill: false,
            // @option fillColor: String = *
            // Fill color. Defaults to the value of the [`color`](#path-color) option
            fillColor: null,
            // @option fillOpacity: Number = 0.2
            // Fill opacity.
            fillOpacity: 0.2,
            // @option fillRule: String = 'evenodd'
            // A string that defines [how the inside of a shape](https://developer.mozilla.org/docs/Web/SVG/Attribute/fill-rule) is determined.
            fillRule: "evenodd",
            // className: '',
            // Option inherited from "Interactive layer" abstract class
            interactive: true,
            // @option bubblingMouseEvents: Boolean = true
            // When `true`, a mouse event on this path will trigger the same event on the map
            // (unless [`L.DomEvent.stopPropagation`](#domevent-stoppropagation) is used).
            bubblingMouseEvents: true
          },
          beforeAdd: function(map2) {
            this._renderer = map2.getRenderer(this);
          },
          onAdd: function() {
            this._renderer._initPath(this);
            this._reset();
            this._renderer._addPath(this);
          },
          onRemove: function() {
            this._renderer._removePath(this);
          },
          // @method redraw(): this
          // Redraws the layer. Sometimes useful after you changed the coordinates that the path uses.
          redraw: function() {
            if (this._map) {
              this._renderer._updatePath(this);
            }
            return this;
          },
          // @method setStyle(style: Path options): this
          // Changes the appearance of a Path based on the options in the `Path options` object.
          setStyle: function(style2) {
            setOptions(this, style2);
            if (this._renderer) {
              this._renderer._updateStyle(this);
              if (this.options.stroke && style2 && Object.prototype.hasOwnProperty.call(style2, "weight")) {
                this._updateBounds();
              }
            }
            return this;
          },
          // @method bringToFront(): this
          // Brings the layer to the top of all path layers.
          bringToFront: function() {
            if (this._renderer) {
              this._renderer._bringToFront(this);
            }
            return this;
          },
          // @method bringToBack(): this
          // Brings the layer to the bottom of all path layers.
          bringToBack: function() {
            if (this._renderer) {
              this._renderer._bringToBack(this);
            }
            return this;
          },
          getElement: function() {
            return this._path;
          },
          _reset: function() {
            this._project();
            this._update();
          },
          _clickTolerance: function() {
            return (this.options.stroke ? this.options.weight / 2 : 0) + (this._renderer.options.tolerance || 0);
          }
        });
        var CircleMarker = Path.extend({
          // @section
          // @aka CircleMarker options
          options: {
            fill: true,
            // @option radius: Number = 10
            // Radius of the circle marker, in pixels
            radius: 10
          },
          initialize: function(latlng, options) {
            setOptions(this, options);
            this._latlng = toLatLng(latlng);
            this._radius = this.options.radius;
          },
          // @method setLatLng(latLng: LatLng): this
          // Sets the position of a circle marker to a new location.
          setLatLng: function(latlng) {
            var oldLatLng = this._latlng;
            this._latlng = toLatLng(latlng);
            this.redraw();
            return this.fire("move", { oldLatLng, latlng: this._latlng });
          },
          // @method getLatLng(): LatLng
          // Returns the current geographical position of the circle marker
          getLatLng: function() {
            return this._latlng;
          },
          // @method setRadius(radius: Number): this
          // Sets the radius of a circle marker. Units are in pixels.
          setRadius: function(radius2) {
            this.options.radius = this._radius = radius2;
            return this.redraw();
          },
          // @method getRadius(): Number
          // Returns the current radius of the circle
          getRadius: function() {
            return this._radius;
          },
          setStyle: function(options) {
            var radius2 = options && options.radius || this._radius;
            Path.prototype.setStyle.call(this, options);
            this.setRadius(radius2);
            return this;
          },
          _project: function() {
            this._point = this._map.latLngToLayerPoint(this._latlng);
            this._updateBounds();
          },
          _updateBounds: function() {
            var r = this._radius, r2 = this._radiusY || r, w = this._clickTolerance(), p = [r + w, r2 + w];
            this._pxBounds = new Bounds(this._point.subtract(p), this._point.add(p));
          },
          _update: function() {
            if (this._map) {
              this._updatePath();
            }
          },
          _updatePath: function() {
            this._renderer._updateCircle(this);
          },
          _empty: function() {
            return this._radius && !this._renderer._bounds.intersects(this._pxBounds);
          },
          // Needed by the `Canvas` renderer for interactivity
          _containsPoint: function(p) {
            return p.distanceTo(this._point) <= this._radius + this._clickTolerance();
          }
        });
        function circleMarker(latlng, options) {
          return new CircleMarker(latlng, options);
        }
        var Circle = CircleMarker.extend({
          initialize: function(latlng, options, legacyOptions) {
            if (typeof options === "number") {
              options = extend({}, legacyOptions, { radius: options });
            }
            setOptions(this, options);
            this._latlng = toLatLng(latlng);
            if (isNaN(this.options.radius)) {
              throw new Error("Circle radius cannot be NaN");
            }
            this._mRadius = this.options.radius;
          },
          // @method setRadius(radius: Number): this
          // Sets the radius of a circle. Units are in meters.
          setRadius: function(radius2) {
            this._mRadius = radius2;
            return this.redraw();
          },
          // @method getRadius(): Number
          // Returns the current radius of a circle. Units are in meters.
          getRadius: function() {
            return this._mRadius;
          },
          // @method getBounds(): LatLngBounds
          // Returns the `LatLngBounds` of the path.
          getBounds: function() {
            var half = [this._radius, this._radiusY || this._radius];
            return new LatLngBounds(
              this._map.layerPointToLatLng(this._point.subtract(half)),
              this._map.layerPointToLatLng(this._point.add(half))
            );
          },
          setStyle: Path.prototype.setStyle,
          _project: function() {
            var lng = this._latlng.lng, lat = this._latlng.lat, map2 = this._map, crs = map2.options.crs;
            if (crs.distance === Earth.distance) {
              var d = Math.PI / 180, latR = this._mRadius / Earth.R / d, top = map2.project([lat + latR, lng]), bottom = map2.project([lat - latR, lng]), p = top.add(bottom).divideBy(2), lat2 = map2.unproject(p).lat, lngR = Math.acos((Math.cos(latR * d) - Math.sin(lat * d) * Math.sin(lat2 * d)) / (Math.cos(lat * d) * Math.cos(lat2 * d))) / d;
              if (isNaN(lngR) || lngR === 0) {
                lngR = latR / Math.cos(Math.PI / 180 * lat);
              }
              this._point = p.subtract(map2.getPixelOrigin());
              this._radius = isNaN(lngR) ? 0 : p.x - map2.project([lat2, lng - lngR]).x;
              this._radiusY = p.y - top.y;
            } else {
              var latlng2 = crs.unproject(crs.project(this._latlng).subtract([this._mRadius, 0]));
              this._point = map2.latLngToLayerPoint(this._latlng);
              this._radius = this._point.x - map2.latLngToLayerPoint(latlng2).x;
            }
            this._updateBounds();
          }
        });
        function circle(latlng, options, legacyOptions) {
          return new Circle(latlng, options, legacyOptions);
        }
        var Polyline = Path.extend({
          // @section
          // @aka Polyline options
          options: {
            // @option smoothFactor: Number = 1.0
            // How much to simplify the polyline on each zoom level. More means
            // better performance and smoother look, and less means more accurate representation.
            smoothFactor: 1,
            // @option noClip: Boolean = false
            // Disable polyline clipping.
            noClip: false
          },
          initialize: function(latlngs, options) {
            setOptions(this, options);
            this._setLatLngs(latlngs);
          },
          // @method getLatLngs(): LatLng[]
          // Returns an array of the points in the path, or nested arrays of points in case of multi-polyline.
          getLatLngs: function() {
            return this._latlngs;
          },
          // @method setLatLngs(latlngs: LatLng[]): this
          // Replaces all the points in the polyline with the given array of geographical points.
          setLatLngs: function(latlngs) {
            this._setLatLngs(latlngs);
            return this.redraw();
          },
          // @method isEmpty(): Boolean
          // Returns `true` if the Polyline has no LatLngs.
          isEmpty: function() {
            return !this._latlngs.length;
          },
          // @method closestLayerPoint(p: Point): Point
          // Returns the point closest to `p` on the Polyline.
          closestLayerPoint: function(p) {
            var minDistance = Infinity, minPoint = null, closest = _sqClosestPointOnSegment, p1, p2;
            for (var j = 0, jLen = this._parts.length; j < jLen; j++) {
              var points = this._parts[j];
              for (var i = 1, len = points.length; i < len; i++) {
                p1 = points[i - 1];
                p2 = points[i];
                var sqDist = closest(p, p1, p2, true);
                if (sqDist < minDistance) {
                  minDistance = sqDist;
                  minPoint = closest(p, p1, p2);
                }
              }
            }
            if (minPoint) {
              minPoint.distance = Math.sqrt(minDistance);
            }
            return minPoint;
          },
          // @method getCenter(): LatLng
          // Returns the center ([centroid](https://en.wikipedia.org/wiki/Centroid)) of the polyline.
          getCenter: function() {
            if (!this._map) {
              throw new Error("Must add layer to map before using getCenter()");
            }
            return polylineCenter(this._defaultShape(), this._map.options.crs);
          },
          // @method getBounds(): LatLngBounds
          // Returns the `LatLngBounds` of the path.
          getBounds: function() {
            return this._bounds;
          },
          // @method addLatLng(latlng: LatLng, latlngs?: LatLng[]): this
          // Adds a given point to the polyline. By default, adds to the first ring of
          // the polyline in case of a multi-polyline, but can be overridden by passing
          // a specific ring as a LatLng array (that you can earlier access with [`getLatLngs`](#polyline-getlatlngs)).
          addLatLng: function(latlng, latlngs) {
            latlngs = latlngs || this._defaultShape();
            latlng = toLatLng(latlng);
            latlngs.push(latlng);
            this._bounds.extend(latlng);
            return this.redraw();
          },
          _setLatLngs: function(latlngs) {
            this._bounds = new LatLngBounds();
            this._latlngs = this._convertLatLngs(latlngs);
          },
          _defaultShape: function() {
            return isFlat(this._latlngs) ? this._latlngs : this._latlngs[0];
          },
          // recursively convert latlngs input into actual LatLng instances; calculate bounds along the way
          _convertLatLngs: function(latlngs) {
            var result = [], flat = isFlat(latlngs);
            for (var i = 0, len = latlngs.length; i < len; i++) {
              if (flat) {
                result[i] = toLatLng(latlngs[i]);
                this._bounds.extend(result[i]);
              } else {
                result[i] = this._convertLatLngs(latlngs[i]);
              }
            }
            return result;
          },
          _project: function() {
            var pxBounds = new Bounds();
            this._rings = [];
            this._projectLatlngs(this._latlngs, this._rings, pxBounds);
            if (this._bounds.isValid() && pxBounds.isValid()) {
              this._rawPxBounds = pxBounds;
              this._updateBounds();
            }
          },
          _updateBounds: function() {
            var w = this._clickTolerance(), p = new Point(w, w);
            if (!this._rawPxBounds) {
              return;
            }
            this._pxBounds = new Bounds([
              this._rawPxBounds.min.subtract(p),
              this._rawPxBounds.max.add(p)
            ]);
          },
          // recursively turns latlngs into a set of rings with projected coordinates
          _projectLatlngs: function(latlngs, result, projectedBounds) {
            var flat = latlngs[0] instanceof LatLng, len = latlngs.length, i, ring;
            if (flat) {
              ring = [];
              for (i = 0; i < len; i++) {
                ring[i] = this._map.latLngToLayerPoint(latlngs[i]);
                projectedBounds.extend(ring[i]);
              }
              result.push(ring);
            } else {
              for (i = 0; i < len; i++) {
                this._projectLatlngs(latlngs[i], result, projectedBounds);
              }
            }
          },
          // clip polyline by renderer bounds so that we have less to render for performance
          _clipPoints: function() {
            var bounds = this._renderer._bounds;
            this._parts = [];
            if (!this._pxBounds || !this._pxBounds.intersects(bounds)) {
              return;
            }
            if (this.options.noClip) {
              this._parts = this._rings;
              return;
            }
            var parts = this._parts, i, j, k, len, len2, segment, points;
            for (i = 0, k = 0, len = this._rings.length; i < len; i++) {
              points = this._rings[i];
              for (j = 0, len2 = points.length; j < len2 - 1; j++) {
                segment = clipSegment(points[j], points[j + 1], bounds, j, true);
                if (!segment) {
                  continue;
                }
                parts[k] = parts[k] || [];
                parts[k].push(segment[0]);
                if (segment[1] !== points[j + 1] || j === len2 - 2) {
                  parts[k].push(segment[1]);
                  k++;
                }
              }
            }
          },
          // simplify each clipped part of the polyline for performance
          _simplifyPoints: function() {
            var parts = this._parts, tolerance = this.options.smoothFactor;
            for (var i = 0, len = parts.length; i < len; i++) {
              parts[i] = simplify(parts[i], tolerance);
            }
          },
          _update: function() {
            if (!this._map) {
              return;
            }
            this._clipPoints();
            this._simplifyPoints();
            this._updatePath();
          },
          _updatePath: function() {
            this._renderer._updatePoly(this);
          },
          // Needed by the `Canvas` renderer for interactivity
          _containsPoint: function(p, closed) {
            var i, j, k, len, len2, part, w = this._clickTolerance();
            if (!this._pxBounds || !this._pxBounds.contains(p)) {
              return false;
            }
            for (i = 0, len = this._parts.length; i < len; i++) {
              part = this._parts[i];
              for (j = 0, len2 = part.length, k = len2 - 1; j < len2; k = j++) {
                if (!closed && j === 0) {
                  continue;
                }
                if (pointToSegmentDistance(p, part[k], part[j]) <= w) {
                  return true;
                }
              }
            }
            return false;
          }
        });
        function polyline(latlngs, options) {
          return new Polyline(latlngs, options);
        }
        Polyline._flat = _flat;
        var Polygon = Polyline.extend({
          options: {
            fill: true
          },
          isEmpty: function() {
            return !this._latlngs.length || !this._latlngs[0].length;
          },
          // @method getCenter(): LatLng
          // Returns the center ([centroid](http://en.wikipedia.org/wiki/Centroid)) of the Polygon.
          getCenter: function() {
            if (!this._map) {
              throw new Error("Must add layer to map before using getCenter()");
            }
            return polygonCenter(this._defaultShape(), this._map.options.crs);
          },
          _convertLatLngs: function(latlngs) {
            var result = Polyline.prototype._convertLatLngs.call(this, latlngs), len = result.length;
            if (len >= 2 && result[0] instanceof LatLng && result[0].equals(result[len - 1])) {
              result.pop();
            }
            return result;
          },
          _setLatLngs: function(latlngs) {
            Polyline.prototype._setLatLngs.call(this, latlngs);
            if (isFlat(this._latlngs)) {
              this._latlngs = [this._latlngs];
            }
          },
          _defaultShape: function() {
            return isFlat(this._latlngs[0]) ? this._latlngs[0] : this._latlngs[0][0];
          },
          _clipPoints: function() {
            var bounds = this._renderer._bounds, w = this.options.weight, p = new Point(w, w);
            bounds = new Bounds(bounds.min.subtract(p), bounds.max.add(p));
            this._parts = [];
            if (!this._pxBounds || !this._pxBounds.intersects(bounds)) {
              return;
            }
            if (this.options.noClip) {
              this._parts = this._rings;
              return;
            }
            for (var i = 0, len = this._rings.length, clipped; i < len; i++) {
              clipped = clipPolygon(this._rings[i], bounds, true);
              if (clipped.length) {
                this._parts.push(clipped);
              }
            }
          },
          _updatePath: function() {
            this._renderer._updatePoly(this, true);
          },
          // Needed by the `Canvas` renderer for interactivity
          _containsPoint: function(p) {
            var inside = false, part, p1, p2, i, j, k, len, len2;
            if (!this._pxBounds || !this._pxBounds.contains(p)) {
              return false;
            }
            for (i = 0, len = this._parts.length; i < len; i++) {
              part = this._parts[i];
              for (j = 0, len2 = part.length, k = len2 - 1; j < len2; k = j++) {
                p1 = part[j];
                p2 = part[k];
                if (p1.y > p.y !== p2.y > p.y && p.x < (p2.x - p1.x) * (p.y - p1.y) / (p2.y - p1.y) + p1.x) {
                  inside = !inside;
                }
              }
            }
            return inside || Polyline.prototype._containsPoint.call(this, p, true);
          }
        });
        function polygon(latlngs, options) {
          return new Polygon(latlngs, options);
        }
        var GeoJSON = FeatureGroup.extend({
          /* @section
           * @aka GeoJSON options
           *
           * @option pointToLayer: Function = *
           * A `Function` defining how GeoJSON points spawn Leaflet layers. It is internally
           * called when data is added, passing the GeoJSON point feature and its `LatLng`.
           * The default is to spawn a default `Marker`:
           * ```js
           * function(geoJsonPoint, latlng) {
           * 	return L.marker(latlng);
           * }
           * ```
           *
           * @option style: Function = *
           * A `Function` defining the `Path options` for styling GeoJSON lines and polygons,
           * called internally when data is added.
           * The default value is to not override any defaults:
           * ```js
           * function (geoJsonFeature) {
           * 	return {}
           * }
           * ```
           *
           * @option onEachFeature: Function = *
           * A `Function` that will be called once for each created `Feature`, after it has
           * been created and styled. Useful for attaching events and popups to features.
           * The default is to do nothing with the newly created layers:
           * ```js
           * function (feature, layer) {}
           * ```
           *
           * @option filter: Function = *
           * A `Function` that will be used to decide whether to include a feature or not.
           * The default is to include all features:
           * ```js
           * function (geoJsonFeature) {
           * 	return true;
           * }
           * ```
           * Note: dynamically changing the `filter` option will have effect only on newly
           * added data. It will _not_ re-evaluate already included features.
           *
           * @option coordsToLatLng: Function = *
           * A `Function` that will be used for converting GeoJSON coordinates to `LatLng`s.
           * The default is the `coordsToLatLng` static method.
           *
           * @option markersInheritOptions: Boolean = false
           * Whether default Markers for "Point" type Features inherit from group options.
           */
          initialize: function(geojson, options) {
            setOptions(this, options);
            this._layers = {};
            if (geojson) {
              this.addData(geojson);
            }
          },
          // @method addData( <GeoJSON> data ): this
          // Adds a GeoJSON object to the layer.
          addData: function(geojson) {
            var features = isArray(geojson) ? geojson : geojson.features, i, len, feature;
            if (features) {
              for (i = 0, len = features.length; i < len; i++) {
                feature = features[i];
                if (feature.geometries || feature.geometry || feature.features || feature.coordinates) {
                  this.addData(feature);
                }
              }
              return this;
            }
            var options = this.options;
            if (options.filter && !options.filter(geojson)) {
              return this;
            }
            var layer = geometryToLayer(geojson, options);
            if (!layer) {
              return this;
            }
            layer.feature = asFeature(geojson);
            layer.defaultOptions = layer.options;
            this.resetStyle(layer);
            if (options.onEachFeature) {
              options.onEachFeature(geojson, layer);
            }
            return this.addLayer(layer);
          },
          // @method resetStyle( <Path> layer? ): this
          // Resets the given vector layer's style to the original GeoJSON style, useful for resetting style after hover events.
          // If `layer` is omitted, the style of all features in the current layer is reset.
          resetStyle: function(layer) {
            if (layer === void 0) {
              return this.eachLayer(this.resetStyle, this);
            }
            layer.options = extend({}, layer.defaultOptions);
            this._setLayerStyle(layer, this.options.style);
            return this;
          },
          // @method setStyle( <Function> style ): this
          // Changes styles of GeoJSON vector layers with the given style function.
          setStyle: function(style2) {
            return this.eachLayer(function(layer) {
              this._setLayerStyle(layer, style2);
            }, this);
          },
          _setLayerStyle: function(layer, style2) {
            if (layer.setStyle) {
              if (typeof style2 === "function") {
                style2 = style2(layer.feature);
              }
              layer.setStyle(style2);
            }
          }
        });
        function geometryToLayer(geojson, options) {
          var geometry = geojson.type === "Feature" ? geojson.geometry : geojson, coords = geometry ? geometry.coordinates : null, layers2 = [], pointToLayer = options && options.pointToLayer, _coordsToLatLng = options && options.coordsToLatLng || coordsToLatLng, latlng, latlngs, i, len;
          if (!coords && !geometry) {
            return null;
          }
          switch (geometry.type) {
            case "Point":
              latlng = _coordsToLatLng(coords);
              return _pointToLayer(pointToLayer, geojson, latlng, options);
            case "MultiPoint":
              for (i = 0, len = coords.length; i < len; i++) {
                latlng = _coordsToLatLng(coords[i]);
                layers2.push(_pointToLayer(pointToLayer, geojson, latlng, options));
              }
              return new FeatureGroup(layers2);
            case "LineString":
            case "MultiLineString":
              latlngs = coordsToLatLngs(coords, geometry.type === "LineString" ? 0 : 1, _coordsToLatLng);
              return new Polyline(latlngs, options);
            case "Polygon":
            case "MultiPolygon":
              latlngs = coordsToLatLngs(coords, geometry.type === "Polygon" ? 1 : 2, _coordsToLatLng);
              return new Polygon(latlngs, options);
            case "GeometryCollection":
              for (i = 0, len = geometry.geometries.length; i < len; i++) {
                var geoLayer = geometryToLayer({
                  geometry: geometry.geometries[i],
                  type: "Feature",
                  properties: geojson.properties
                }, options);
                if (geoLayer) {
                  layers2.push(geoLayer);
                }
              }
              return new FeatureGroup(layers2);
            case "FeatureCollection":
              for (i = 0, len = geometry.features.length; i < len; i++) {
                var featureLayer = geometryToLayer(geometry.features[i], options);
                if (featureLayer) {
                  layers2.push(featureLayer);
                }
              }
              return new FeatureGroup(layers2);
            default:
              throw new Error("Invalid GeoJSON object.");
          }
        }
        function _pointToLayer(pointToLayerFn, geojson, latlng, options) {
          return pointToLayerFn ? pointToLayerFn(geojson, latlng) : new Marker(latlng, options && options.markersInheritOptions && options);
        }
        function coordsToLatLng(coords) {
          return new LatLng(coords[1], coords[0], coords[2]);
        }
        function coordsToLatLngs(coords, levelsDeep, _coordsToLatLng) {
          var latlngs = [];
          for (var i = 0, len = coords.length, latlng; i < len; i++) {
            latlng = levelsDeep ? coordsToLatLngs(coords[i], levelsDeep - 1, _coordsToLatLng) : (_coordsToLatLng || coordsToLatLng)(coords[i]);
            latlngs.push(latlng);
          }
          return latlngs;
        }
        function latLngToCoords(latlng, precision) {
          latlng = toLatLng(latlng);
          return latlng.alt !== void 0 ? [formatNum(latlng.lng, precision), formatNum(latlng.lat, precision), formatNum(latlng.alt, precision)] : [formatNum(latlng.lng, precision), formatNum(latlng.lat, precision)];
        }
        function latLngsToCoords(latlngs, levelsDeep, closed, precision) {
          var coords = [];
          for (var i = 0, len = latlngs.length; i < len; i++) {
            coords.push(levelsDeep ? latLngsToCoords(latlngs[i], isFlat(latlngs[i]) ? 0 : levelsDeep - 1, closed, precision) : latLngToCoords(latlngs[i], precision));
          }
          if (!levelsDeep && closed && coords.length > 0) {
            coords.push(coords[0].slice());
          }
          return coords;
        }
        function getFeature(layer, newGeometry) {
          return layer.feature ? extend({}, layer.feature, { geometry: newGeometry }) : asFeature(newGeometry);
        }
        function asFeature(geojson) {
          if (geojson.type === "Feature" || geojson.type === "FeatureCollection") {
            return geojson;
          }
          return {
            type: "Feature",
            properties: {},
            geometry: geojson
          };
        }
        var PointToGeoJSON = {
          toGeoJSON: function(precision) {
            return getFeature(this, {
              type: "Point",
              coordinates: latLngToCoords(this.getLatLng(), precision)
            });
          }
        };
        Marker.include(PointToGeoJSON);
        Circle.include(PointToGeoJSON);
        CircleMarker.include(PointToGeoJSON);
        Polyline.include({
          toGeoJSON: function(precision) {
            var multi = !isFlat(this._latlngs);
            var coords = latLngsToCoords(this._latlngs, multi ? 1 : 0, false, precision);
            return getFeature(this, {
              type: (multi ? "Multi" : "") + "LineString",
              coordinates: coords
            });
          }
        });
        Polygon.include({
          toGeoJSON: function(precision) {
            var holes = !isFlat(this._latlngs), multi = holes && !isFlat(this._latlngs[0]);
            var coords = latLngsToCoords(this._latlngs, multi ? 2 : holes ? 1 : 0, true, precision);
            if (!holes) {
              coords = [coords];
            }
            return getFeature(this, {
              type: (multi ? "Multi" : "") + "Polygon",
              coordinates: coords
            });
          }
        });
        LayerGroup.include({
          toMultiPoint: function(precision) {
            var coords = [];
            this.eachLayer(function(layer) {
              coords.push(layer.toGeoJSON(precision).geometry.coordinates);
            });
            return getFeature(this, {
              type: "MultiPoint",
              coordinates: coords
            });
          },
          // @method toGeoJSON(precision?: Number|false): Object
          // Coordinates values are rounded with [`formatNum`](#util-formatnum) function with given `precision`.
          // Returns a [`GeoJSON`](https://en.wikipedia.org/wiki/GeoJSON) representation of the layer group (as a GeoJSON `FeatureCollection`, `GeometryCollection`, or `MultiPoint`).
          toGeoJSON: function(precision) {
            var type2 = this.feature && this.feature.geometry && this.feature.geometry.type;
            if (type2 === "MultiPoint") {
              return this.toMultiPoint(precision);
            }
            var isGeometryCollection = type2 === "GeometryCollection", jsons = [];
            this.eachLayer(function(layer) {
              if (layer.toGeoJSON) {
                var json = layer.toGeoJSON(precision);
                if (isGeometryCollection) {
                  jsons.push(json.geometry);
                } else {
                  var feature = asFeature(json);
                  if (feature.type === "FeatureCollection") {
                    jsons.push.apply(jsons, feature.features);
                  } else {
                    jsons.push(feature);
                  }
                }
              }
            });
            if (isGeometryCollection) {
              return getFeature(this, {
                geometries: jsons,
                type: "GeometryCollection"
              });
            }
            return {
              type: "FeatureCollection",
              features: jsons
            };
          }
        });
        function geoJSON(geojson, options) {
          return new GeoJSON(geojson, options);
        }
        var geoJson = geoJSON;
        var ImageOverlay = Layer.extend({
          // @section
          // @aka ImageOverlay options
          options: {
            // @option opacity: Number = 1.0
            // The opacity of the image overlay.
            opacity: 1,
            // @option alt: String = ''
            // Text for the `alt` attribute of the image (useful for accessibility).
            alt: "",
            // @option interactive: Boolean = false
            // If `true`, the image overlay will emit [mouse events](#interactive-layer) when clicked or hovered.
            interactive: false,
            // @option crossOrigin: Boolean|String = false
            // Whether the crossOrigin attribute will be added to the image.
            // If a String is provided, the image will have its crossOrigin attribute set to the String provided. This is needed if you want to access image pixel data.
            // Refer to [CORS Settings](https://developer.mozilla.org/en-US/docs/Web/HTML/CORS_settings_attributes) for valid String values.
            crossOrigin: false,
            // @option errorOverlayUrl: String = ''
            // URL to the overlay image to show in place of the overlay that failed to load.
            errorOverlayUrl: "",
            // @option zIndex: Number = 1
            // The explicit [zIndex](https://developer.mozilla.org/docs/Web/CSS/CSS_Positioning/Understanding_z_index) of the overlay layer.
            zIndex: 1,
            // @option className: String = ''
            // A custom class name to assign to the image. Empty by default.
            className: ""
          },
          initialize: function(url, bounds, options) {
            this._url = url;
            this._bounds = toLatLngBounds(bounds);
            setOptions(this, options);
          },
          onAdd: function() {
            if (!this._image) {
              this._initImage();
              if (this.options.opacity < 1) {
                this._updateOpacity();
              }
            }
            if (this.options.interactive) {
              addClass(this._image, "leaflet-interactive");
              this.addInteractiveTarget(this._image);
            }
            this.getPane().appendChild(this._image);
            this._reset();
          },
          onRemove: function() {
            remove(this._image);
            if (this.options.interactive) {
              this.removeInteractiveTarget(this._image);
            }
          },
          // @method setOpacity(opacity: Number): this
          // Sets the opacity of the overlay.
          setOpacity: function(opacity) {
            this.options.opacity = opacity;
            if (this._image) {
              this._updateOpacity();
            }
            return this;
          },
          setStyle: function(styleOpts) {
            if (styleOpts.opacity) {
              this.setOpacity(styleOpts.opacity);
            }
            return this;
          },
          // @method bringToFront(): this
          // Brings the layer to the top of all overlays.
          bringToFront: function() {
            if (this._map) {
              toFront(this._image);
            }
            return this;
          },
          // @method bringToBack(): this
          // Brings the layer to the bottom of all overlays.
          bringToBack: function() {
            if (this._map) {
              toBack(this._image);
            }
            return this;
          },
          // @method setUrl(url: String): this
          // Changes the URL of the image.
          setUrl: function(url) {
            this._url = url;
            if (this._image) {
              this._image.src = url;
            }
            return this;
          },
          // @method setBounds(bounds: LatLngBounds): this
          // Update the bounds that this ImageOverlay covers
          setBounds: function(bounds) {
            this._bounds = toLatLngBounds(bounds);
            if (this._map) {
              this._reset();
            }
            return this;
          },
          getEvents: function() {
            var events = {
              zoom: this._reset,
              viewreset: this._reset
            };
            if (this._zoomAnimated) {
              events.zoomanim = this._animateZoom;
            }
            return events;
          },
          // @method setZIndex(value: Number): this
          // Changes the [zIndex](#imageoverlay-zindex) of the image overlay.
          setZIndex: function(value) {
            this.options.zIndex = value;
            this._updateZIndex();
            return this;
          },
          // @method getBounds(): LatLngBounds
          // Get the bounds that this ImageOverlay covers
          getBounds: function() {
            return this._bounds;
          },
          // @method getElement(): HTMLElement
          // Returns the instance of [`HTMLImageElement`](https://developer.mozilla.org/docs/Web/API/HTMLImageElement)
          // used by this overlay.
          getElement: function() {
            return this._image;
          },
          _initImage: function() {
            var wasElementSupplied = this._url.tagName === "IMG";
            var img = this._image = wasElementSupplied ? this._url : create$1("img");
            addClass(img, "leaflet-image-layer");
            if (this._zoomAnimated) {
              addClass(img, "leaflet-zoom-animated");
            }
            if (this.options.className) {
              addClass(img, this.options.className);
            }
            img.onselectstart = falseFn;
            img.onmousemove = falseFn;
            img.onload = bind(this.fire, this, "load");
            img.onerror = bind(this._overlayOnError, this, "error");
            if (this.options.crossOrigin || this.options.crossOrigin === "") {
              img.crossOrigin = this.options.crossOrigin === true ? "" : this.options.crossOrigin;
            }
            if (this.options.zIndex) {
              this._updateZIndex();
            }
            if (wasElementSupplied) {
              this._url = img.src;
              return;
            }
            img.src = this._url;
            img.alt = this.options.alt;
          },
          _animateZoom: function(e) {
            var scale2 = this._map.getZoomScale(e.zoom), offset = this._map._latLngBoundsToNewLayerBounds(this._bounds, e.zoom, e.center).min;
            setTransform(this._image, offset, scale2);
          },
          _reset: function() {
            var image = this._image, bounds = new Bounds(
              this._map.latLngToLayerPoint(this._bounds.getNorthWest()),
              this._map.latLngToLayerPoint(this._bounds.getSouthEast())
            ), size = bounds.getSize();
            setPosition(image, bounds.min);
            image.style.width = size.x + "px";
            image.style.height = size.y + "px";
          },
          _updateOpacity: function() {
            setOpacity(this._image, this.options.opacity);
          },
          _updateZIndex: function() {
            if (this._image && this.options.zIndex !== void 0 && this.options.zIndex !== null) {
              this._image.style.zIndex = this.options.zIndex;
            }
          },
          _overlayOnError: function() {
            this.fire("error");
            var errorUrl = this.options.errorOverlayUrl;
            if (errorUrl && this._url !== errorUrl) {
              this._url = errorUrl;
              this._image.src = errorUrl;
            }
          },
          // @method getCenter(): LatLng
          // Returns the center of the ImageOverlay.
          getCenter: function() {
            return this._bounds.getCenter();
          }
        });
        var imageOverlay = function(url, bounds, options) {
          return new ImageOverlay(url, bounds, options);
        };
        var VideoOverlay = ImageOverlay.extend({
          // @section
          // @aka VideoOverlay options
          options: {
            // @option autoplay: Boolean = true
            // Whether the video starts playing automatically when loaded.
            // On some browsers autoplay will only work with `muted: true`
            autoplay: true,
            // @option loop: Boolean = true
            // Whether the video will loop back to the beginning when played.
            loop: true,
            // @option keepAspectRatio: Boolean = true
            // Whether the video will save aspect ratio after the projection.
            // Relevant for supported browsers. See [browser compatibility](https://developer.mozilla.org/en-US/docs/Web/CSS/object-fit)
            keepAspectRatio: true,
            // @option muted: Boolean = false
            // Whether the video starts on mute when loaded.
            muted: false,
            // @option playsInline: Boolean = true
            // Mobile browsers will play the video right where it is instead of open it up in fullscreen mode.
            playsInline: true
          },
          _initImage: function() {
            var wasElementSupplied = this._url.tagName === "VIDEO";
            var vid = this._image = wasElementSupplied ? this._url : create$1("video");
            addClass(vid, "leaflet-image-layer");
            if (this._zoomAnimated) {
              addClass(vid, "leaflet-zoom-animated");
            }
            if (this.options.className) {
              addClass(vid, this.options.className);
            }
            vid.onselectstart = falseFn;
            vid.onmousemove = falseFn;
            vid.onloadeddata = bind(this.fire, this, "load");
            if (wasElementSupplied) {
              var sourceElements = vid.getElementsByTagName("source");
              var sources = [];
              for (var j = 0; j < sourceElements.length; j++) {
                sources.push(sourceElements[j].src);
              }
              this._url = sourceElements.length > 0 ? sources : [vid.src];
              return;
            }
            if (!isArray(this._url)) {
              this._url = [this._url];
            }
            if (!this.options.keepAspectRatio && Object.prototype.hasOwnProperty.call(vid.style, "objectFit")) {
              vid.style["objectFit"] = "fill";
            }
            vid.autoplay = !!this.options.autoplay;
            vid.loop = !!this.options.loop;
            vid.muted = !!this.options.muted;
            vid.playsInline = !!this.options.playsInline;
            for (var i = 0; i < this._url.length; i++) {
              var source = create$1("source");
              source.src = this._url[i];
              vid.appendChild(source);
            }
          }
          // @method getElement(): HTMLVideoElement
          // Returns the instance of [`HTMLVideoElement`](https://developer.mozilla.org/docs/Web/API/HTMLVideoElement)
          // used by this overlay.
        });
        function videoOverlay(video, bounds, options) {
          return new VideoOverlay(video, bounds, options);
        }
        var SVGOverlay = ImageOverlay.extend({
          _initImage: function() {
            var el = this._image = this._url;
            addClass(el, "leaflet-image-layer");
            if (this._zoomAnimated) {
              addClass(el, "leaflet-zoom-animated");
            }
            if (this.options.className) {
              addClass(el, this.options.className);
            }
            el.onselectstart = falseFn;
            el.onmousemove = falseFn;
          }
          // @method getElement(): SVGElement
          // Returns the instance of [`SVGElement`](https://developer.mozilla.org/docs/Web/API/SVGElement)
          // used by this overlay.
        });
        function svgOverlay(el, bounds, options) {
          return new SVGOverlay(el, bounds, options);
        }
        var DivOverlay = Layer.extend({
          // @section
          // @aka DivOverlay options
          options: {
            // @option interactive: Boolean = false
            // If true, the popup/tooltip will listen to the mouse events.
            interactive: false,
            // @option offset: Point = Point(0, 0)
            // The offset of the overlay position.
            offset: [0, 0],
            // @option className: String = ''
            // A custom CSS class name to assign to the overlay.
            className: "",
            // @option pane: String = undefined
            // `Map pane` where the overlay will be added.
            pane: void 0,
            // @option content: String|HTMLElement|Function = ''
            // Sets the HTML content of the overlay while initializing. If a function is passed the source layer will be
            // passed to the function. The function should return a `String` or `HTMLElement` to be used in the overlay.
            content: ""
          },
          initialize: function(options, source) {
            if (options && (options instanceof LatLng || isArray(options))) {
              this._latlng = toLatLng(options);
              setOptions(this, source);
            } else {
              setOptions(this, options);
              this._source = source;
            }
            if (this.options.content) {
              this._content = this.options.content;
            }
          },
          // @method openOn(map: Map): this
          // Adds the overlay to the map.
          // Alternative to `map.openPopup(popup)`/`.openTooltip(tooltip)`.
          openOn: function(map2) {
            map2 = arguments.length ? map2 : this._source._map;
            if (!map2.hasLayer(this)) {
              map2.addLayer(this);
            }
            return this;
          },
          // @method close(): this
          // Closes the overlay.
          // Alternative to `map.closePopup(popup)`/`.closeTooltip(tooltip)`
          // and `layer.closePopup()`/`.closeTooltip()`.
          close: function() {
            if (this._map) {
              this._map.removeLayer(this);
            }
            return this;
          },
          // @method toggle(layer?: Layer): this
          // Opens or closes the overlay bound to layer depending on its current state.
          // Argument may be omitted only for overlay bound to layer.
          // Alternative to `layer.togglePopup()`/`.toggleTooltip()`.
          toggle: function(layer) {
            if (this._map) {
              this.close();
            } else {
              if (arguments.length) {
                this._source = layer;
              } else {
                layer = this._source;
              }
              this._prepareOpen();
              this.openOn(layer._map);
            }
            return this;
          },
          onAdd: function(map2) {
            this._zoomAnimated = map2._zoomAnimated;
            if (!this._container) {
              this._initLayout();
            }
            if (map2._fadeAnimated) {
              setOpacity(this._container, 0);
            }
            clearTimeout(this._removeTimeout);
            this.getPane().appendChild(this._container);
            this.update();
            if (map2._fadeAnimated) {
              setOpacity(this._container, 1);
            }
            this.bringToFront();
            if (this.options.interactive) {
              addClass(this._container, "leaflet-interactive");
              this.addInteractiveTarget(this._container);
            }
          },
          onRemove: function(map2) {
            if (map2._fadeAnimated) {
              setOpacity(this._container, 0);
              this._removeTimeout = setTimeout(bind(remove, void 0, this._container), 200);
            } else {
              remove(this._container);
            }
            if (this.options.interactive) {
              removeClass(this._container, "leaflet-interactive");
              this.removeInteractiveTarget(this._container);
            }
          },
          // @namespace DivOverlay
          // @method getLatLng: LatLng
          // Returns the geographical point of the overlay.
          getLatLng: function() {
            return this._latlng;
          },
          // @method setLatLng(latlng: LatLng): this
          // Sets the geographical point where the overlay will open.
          setLatLng: function(latlng) {
            this._latlng = toLatLng(latlng);
            if (this._map) {
              this._updatePosition();
              this._adjustPan();
            }
            return this;
          },
          // @method getContent: String|HTMLElement
          // Returns the content of the overlay.
          getContent: function() {
            return this._content;
          },
          // @method setContent(htmlContent: String|HTMLElement|Function): this
          // Sets the HTML content of the overlay. If a function is passed the source layer will be passed to the function.
          // The function should return a `String` or `HTMLElement` to be used in the overlay.
          setContent: function(content) {
            this._content = content;
            this.update();
            return this;
          },
          // @method getElement: String|HTMLElement
          // Returns the HTML container of the overlay.
          getElement: function() {
            return this._container;
          },
          // @method update: null
          // Updates the overlay content, layout and position. Useful for updating the overlay after something inside changed, e.g. image loaded.
          update: function() {
            if (!this._map) {
              return;
            }
            this._container.style.visibility = "hidden";
            this._updateContent();
            this._updateLayout();
            this._updatePosition();
            this._container.style.visibility = "";
            this._adjustPan();
          },
          getEvents: function() {
            var events = {
              zoom: this._updatePosition,
              viewreset: this._updatePosition
            };
            if (this._zoomAnimated) {
              events.zoomanim = this._animateZoom;
            }
            return events;
          },
          // @method isOpen: Boolean
          // Returns `true` when the overlay is visible on the map.
          isOpen: function() {
            return !!this._map && this._map.hasLayer(this);
          },
          // @method bringToFront: this
          // Brings this overlay in front of other overlays (in the same map pane).
          bringToFront: function() {
            if (this._map) {
              toFront(this._container);
            }
            return this;
          },
          // @method bringToBack: this
          // Brings this overlay to the back of other overlays (in the same map pane).
          bringToBack: function() {
            if (this._map) {
              toBack(this._container);
            }
            return this;
          },
          // prepare bound overlay to open: update latlng pos / content source (for FeatureGroup)
          _prepareOpen: function(latlng) {
            var source = this._source;
            if (!source._map) {
              return false;
            }
            if (source instanceof FeatureGroup) {
              source = null;
              var layers2 = this._source._layers;
              for (var id in layers2) {
                if (layers2[id]._map) {
                  source = layers2[id];
                  break;
                }
              }
              if (!source) {
                return false;
              }
              this._source = source;
            }
            if (!latlng) {
              if (source.getCenter) {
                latlng = source.getCenter();
              } else if (source.getLatLng) {
                latlng = source.getLatLng();
              } else if (source.getBounds) {
                latlng = source.getBounds().getCenter();
              } else {
                throw new Error("Unable to get source layer LatLng.");
              }
            }
            this.setLatLng(latlng);
            if (this._map) {
              this.update();
            }
            return true;
          },
          _updateContent: function() {
            if (!this._content) {
              return;
            }
            var node = this._contentNode;
            var content = typeof this._content === "function" ? this._content(this._source || this) : this._content;
            if (typeof content === "string") {
              node.innerHTML = content;
            } else {
              while (node.hasChildNodes()) {
                node.removeChild(node.firstChild);
              }
              node.appendChild(content);
            }
            this.fire("contentupdate");
          },
          _updatePosition: function() {
            if (!this._map) {
              return;
            }
            var pos = this._map.latLngToLayerPoint(this._latlng), offset = toPoint(this.options.offset), anchor = this._getAnchor();
            if (this._zoomAnimated) {
              setPosition(this._container, pos.add(anchor));
            } else {
              offset = offset.add(pos).add(anchor);
            }
            var bottom = this._containerBottom = -offset.y, left = this._containerLeft = -Math.round(this._containerWidth / 2) + offset.x;
            this._container.style.bottom = bottom + "px";
            this._container.style.left = left + "px";
          },
          _getAnchor: function() {
            return [0, 0];
          }
        });
        Map3.include({
          _initOverlay: function(OverlayClass, content, latlng, options) {
            var overlay = content;
            if (!(overlay instanceof OverlayClass)) {
              overlay = new OverlayClass(options).setContent(content);
            }
            if (latlng) {
              overlay.setLatLng(latlng);
            }
            return overlay;
          }
        });
        Layer.include({
          _initOverlay: function(OverlayClass, old, content, options) {
            var overlay = content;
            if (overlay instanceof OverlayClass) {
              setOptions(overlay, options);
              overlay._source = this;
            } else {
              overlay = old && !options ? old : new OverlayClass(options, this);
              overlay.setContent(content);
            }
            return overlay;
          }
        });
        var Popup = DivOverlay.extend({
          // @section
          // @aka Popup options
          options: {
            // @option pane: String = 'popupPane'
            // `Map pane` where the popup will be added.
            pane: "popupPane",
            // @option offset: Point = Point(0, 7)
            // The offset of the popup position.
            offset: [0, 7],
            // @option maxWidth: Number = 300
            // Max width of the popup, in pixels.
            maxWidth: 300,
            // @option minWidth: Number = 50
            // Min width of the popup, in pixels.
            minWidth: 50,
            // @option maxHeight: Number = null
            // If set, creates a scrollable container of the given height
            // inside a popup if its content exceeds it.
            // The scrollable container can be styled using the
            // `leaflet-popup-scrolled` CSS class selector.
            maxHeight: null,
            // @option autoPan: Boolean = true
            // Set it to `false` if you don't want the map to do panning animation
            // to fit the opened popup.
            autoPan: true,
            // @option autoPanPaddingTopLeft: Point = null
            // The margin between the popup and the top left corner of the map
            // view after autopanning was performed.
            autoPanPaddingTopLeft: null,
            // @option autoPanPaddingBottomRight: Point = null
            // The margin between the popup and the bottom right corner of the map
            // view after autopanning was performed.
            autoPanPaddingBottomRight: null,
            // @option autoPanPadding: Point = Point(5, 5)
            // Equivalent of setting both top left and bottom right autopan padding to the same value.
            autoPanPadding: [5, 5],
            // @option keepInView: Boolean = false
            // Set it to `true` if you want to prevent users from panning the popup
            // off of the screen while it is open.
            keepInView: false,
            // @option closeButton: Boolean = true
            // Controls the presence of a close button in the popup.
            closeButton: true,
            // @option autoClose: Boolean = true
            // Set it to `false` if you want to override the default behavior of
            // the popup closing when another popup is opened.
            autoClose: true,
            // @option closeOnEscapeKey: Boolean = true
            // Set it to `false` if you want to override the default behavior of
            // the ESC key for closing of the popup.
            closeOnEscapeKey: true,
            // @option closeOnClick: Boolean = *
            // Set it if you want to override the default behavior of the popup closing when user clicks
            // on the map. Defaults to the map's [`closePopupOnClick`](#map-closepopuponclick) option.
            // @option className: String = ''
            // A custom CSS class name to assign to the popup.
            className: ""
          },
          // @namespace Popup
          // @method openOn(map: Map): this
          // Alternative to `map.openPopup(popup)`.
          // Adds the popup to the map and closes the previous one.
          openOn: function(map2) {
            map2 = arguments.length ? map2 : this._source._map;
            if (!map2.hasLayer(this) && map2._popup && map2._popup.options.autoClose) {
              map2.removeLayer(map2._popup);
            }
            map2._popup = this;
            return DivOverlay.prototype.openOn.call(this, map2);
          },
          onAdd: function(map2) {
            DivOverlay.prototype.onAdd.call(this, map2);
            map2.fire("popupopen", { popup: this });
            if (this._source) {
              this._source.fire("popupopen", { popup: this }, true);
              if (!(this._source instanceof Path)) {
                this._source.on("preclick", stopPropagation);
              }
            }
          },
          onRemove: function(map2) {
            DivOverlay.prototype.onRemove.call(this, map2);
            map2.fire("popupclose", { popup: this });
            if (this._source) {
              this._source.fire("popupclose", { popup: this }, true);
              if (!(this._source instanceof Path)) {
                this._source.off("preclick", stopPropagation);
              }
            }
          },
          getEvents: function() {
            var events = DivOverlay.prototype.getEvents.call(this);
            if (this.options.closeOnClick !== void 0 ? this.options.closeOnClick : this._map.options.closePopupOnClick) {
              events.preclick = this.close;
            }
            if (this.options.keepInView) {
              events.moveend = this._adjustPan;
            }
            return events;
          },
          _initLayout: function() {
            var prefix = "leaflet-popup", container = this._container = create$1(
              "div",
              prefix + " " + (this.options.className || "") + " leaflet-zoom-animated"
            );
            var wrapper = this._wrapper = create$1("div", prefix + "-content-wrapper", container);
            this._contentNode = create$1("div", prefix + "-content", wrapper);
            disableClickPropagation(container);
            disableScrollPropagation(this._contentNode);
            on(container, "contextmenu", stopPropagation);
            this._tipContainer = create$1("div", prefix + "-tip-container", container);
            this._tip = create$1("div", prefix + "-tip", this._tipContainer);
            if (this.options.closeButton) {
              var closeButton = this._closeButton = create$1("a", prefix + "-close-button", container);
              closeButton.setAttribute("role", "button");
              closeButton.setAttribute("aria-label", "Close popup");
              closeButton.href = "#close";
              closeButton.innerHTML = '<span aria-hidden="true">&#215;</span>';
              on(closeButton, "click", function(ev) {
                preventDefault(ev);
                this.close();
              }, this);
            }
          },
          _updateLayout: function() {
            var container = this._contentNode, style2 = container.style;
            style2.width = "";
            style2.whiteSpace = "nowrap";
            var width = container.offsetWidth;
            width = Math.min(width, this.options.maxWidth);
            width = Math.max(width, this.options.minWidth);
            style2.width = width + 1 + "px";
            style2.whiteSpace = "";
            style2.height = "";
            var height = container.offsetHeight, maxHeight = this.options.maxHeight, scrolledClass = "leaflet-popup-scrolled";
            if (maxHeight && height > maxHeight) {
              style2.height = maxHeight + "px";
              addClass(container, scrolledClass);
            } else {
              removeClass(container, scrolledClass);
            }
            this._containerWidth = this._container.offsetWidth;
          },
          _animateZoom: function(e) {
            var pos = this._map._latLngToNewLayerPoint(this._latlng, e.zoom, e.center), anchor = this._getAnchor();
            setPosition(this._container, pos.add(anchor));
          },
          _adjustPan: function() {
            if (!this.options.autoPan) {
              return;
            }
            if (this._map._panAnim) {
              this._map._panAnim.stop();
            }
            if (this._autopanning) {
              this._autopanning = false;
              return;
            }
            var map2 = this._map, marginBottom = parseInt(getStyle(this._container, "marginBottom"), 10) || 0, containerHeight = this._container.offsetHeight + marginBottom, containerWidth = this._containerWidth, layerPos = new Point(this._containerLeft, -containerHeight - this._containerBottom);
            layerPos._add(getPosition(this._container));
            var containerPos = map2.layerPointToContainerPoint(layerPos), padding = toPoint(this.options.autoPanPadding), paddingTL = toPoint(this.options.autoPanPaddingTopLeft || padding), paddingBR = toPoint(this.options.autoPanPaddingBottomRight || padding), size = map2.getSize(), dx = 0, dy = 0;
            if (containerPos.x + containerWidth + paddingBR.x > size.x) {
              dx = containerPos.x + containerWidth - size.x + paddingBR.x;
            }
            if (containerPos.x - dx - paddingTL.x < 0) {
              dx = containerPos.x - paddingTL.x;
            }
            if (containerPos.y + containerHeight + paddingBR.y > size.y) {
              dy = containerPos.y + containerHeight - size.y + paddingBR.y;
            }
            if (containerPos.y - dy - paddingTL.y < 0) {
              dy = containerPos.y - paddingTL.y;
            }
            if (dx || dy) {
              if (this.options.keepInView) {
                this._autopanning = true;
              }
              map2.fire("autopanstart").panBy([dx, dy]);
            }
          },
          _getAnchor: function() {
            return toPoint(this._source && this._source._getPopupAnchor ? this._source._getPopupAnchor() : [0, 0]);
          }
        });
        var popup = function(options, source) {
          return new Popup(options, source);
        };
        Map3.mergeOptions({
          closePopupOnClick: true
        });
        Map3.include({
          // @method openPopup(popup: Popup): this
          // Opens the specified popup while closing the previously opened (to make sure only one is opened at one time for usability).
          // @alternative
          // @method openPopup(content: String|HTMLElement, latlng: LatLng, options?: Popup options): this
          // Creates a popup with the specified content and options and opens it in the given point on a map.
          openPopup: function(popup2, latlng, options) {
            this._initOverlay(Popup, popup2, latlng, options).openOn(this);
            return this;
          },
          // @method closePopup(popup?: Popup): this
          // Closes the popup previously opened with [openPopup](#map-openpopup) (or the given one).
          closePopup: function(popup2) {
            popup2 = arguments.length ? popup2 : this._popup;
            if (popup2) {
              popup2.close();
            }
            return this;
          }
        });
        Layer.include({
          // @method bindPopup(content: String|HTMLElement|Function|Popup, options?: Popup options): this
          // Binds a popup to the layer with the passed `content` and sets up the
          // necessary event listeners. If a `Function` is passed it will receive
          // the layer as the first argument and should return a `String` or `HTMLElement`.
          bindPopup: function(content, options) {
            this._popup = this._initOverlay(Popup, this._popup, content, options);
            if (!this._popupHandlersAdded) {
              this.on({
                click: this._openPopup,
                keypress: this._onKeyPress,
                remove: this.closePopup,
                move: this._movePopup
              });
              this._popupHandlersAdded = true;
            }
            return this;
          },
          // @method unbindPopup(): this
          // Removes the popup previously bound with `bindPopup`.
          unbindPopup: function() {
            if (this._popup) {
              this.off({
                click: this._openPopup,
                keypress: this._onKeyPress,
                remove: this.closePopup,
                move: this._movePopup
              });
              this._popupHandlersAdded = false;
              this._popup = null;
            }
            return this;
          },
          // @method openPopup(latlng?: LatLng): this
          // Opens the bound popup at the specified `latlng` or at the default popup anchor if no `latlng` is passed.
          openPopup: function(latlng) {
            if (this._popup) {
              if (!(this instanceof FeatureGroup)) {
                this._popup._source = this;
              }
              if (this._popup._prepareOpen(latlng || this._latlng)) {
                this._popup.openOn(this._map);
              }
            }
            return this;
          },
          // @method closePopup(): this
          // Closes the popup bound to this layer if it is open.
          closePopup: function() {
            if (this._popup) {
              this._popup.close();
            }
            return this;
          },
          // @method togglePopup(): this
          // Opens or closes the popup bound to this layer depending on its current state.
          togglePopup: function() {
            if (this._popup) {
              this._popup.toggle(this);
            }
            return this;
          },
          // @method isPopupOpen(): boolean
          // Returns `true` if the popup bound to this layer is currently open.
          isPopupOpen: function() {
            return this._popup ? this._popup.isOpen() : false;
          },
          // @method setPopupContent(content: String|HTMLElement|Popup): this
          // Sets the content of the popup bound to this layer.
          setPopupContent: function(content) {
            if (this._popup) {
              this._popup.setContent(content);
            }
            return this;
          },
          // @method getPopup(): Popup
          // Returns the popup bound to this layer.
          getPopup: function() {
            return this._popup;
          },
          _openPopup: function(e) {
            if (!this._popup || !this._map) {
              return;
            }
            stop(e);
            var target = e.layer || e.target;
            if (this._popup._source === target && !(target instanceof Path)) {
              if (this._map.hasLayer(this._popup)) {
                this.closePopup();
              } else {
                this.openPopup(e.latlng);
              }
              return;
            }
            this._popup._source = target;
            this.openPopup(e.latlng);
          },
          _movePopup: function(e) {
            this._popup.setLatLng(e.latlng);
          },
          _onKeyPress: function(e) {
            if (e.originalEvent.keyCode === 13) {
              this._openPopup(e);
            }
          }
        });
        var Tooltip = DivOverlay.extend({
          // @section
          // @aka Tooltip options
          options: {
            // @option pane: String = 'tooltipPane'
            // `Map pane` where the tooltip will be added.
            pane: "tooltipPane",
            // @option offset: Point = Point(0, 0)
            // Optional offset of the tooltip position.
            offset: [0, 0],
            // @option direction: String = 'auto'
            // Direction where to open the tooltip. Possible values are: `right`, `left`,
            // `top`, `bottom`, `center`, `auto`.
            // `auto` will dynamically switch between `right` and `left` according to the tooltip
            // position on the map.
            direction: "auto",
            // @option permanent: Boolean = false
            // Whether to open the tooltip permanently or only on mouseover.
            permanent: false,
            // @option sticky: Boolean = false
            // If true, the tooltip will follow the mouse instead of being fixed at the feature center.
            sticky: false,
            // @option opacity: Number = 0.9
            // Tooltip container opacity.
            opacity: 0.9
          },
          onAdd: function(map2) {
            DivOverlay.prototype.onAdd.call(this, map2);
            this.setOpacity(this.options.opacity);
            map2.fire("tooltipopen", { tooltip: this });
            if (this._source) {
              this.addEventParent(this._source);
              this._source.fire("tooltipopen", { tooltip: this }, true);
            }
          },
          onRemove: function(map2) {
            DivOverlay.prototype.onRemove.call(this, map2);
            map2.fire("tooltipclose", { tooltip: this });
            if (this._source) {
              this.removeEventParent(this._source);
              this._source.fire("tooltipclose", { tooltip: this }, true);
            }
          },
          getEvents: function() {
            var events = DivOverlay.prototype.getEvents.call(this);
            if (!this.options.permanent) {
              events.preclick = this.close;
            }
            return events;
          },
          _initLayout: function() {
            var prefix = "leaflet-tooltip", className = prefix + " " + (this.options.className || "") + " leaflet-zoom-" + (this._zoomAnimated ? "animated" : "hide");
            this._contentNode = this._container = create$1("div", className);
            this._container.setAttribute("role", "tooltip");
            this._container.setAttribute("id", "leaflet-tooltip-" + stamp(this));
          },
          _updateLayout: function() {
          },
          _adjustPan: function() {
          },
          _setPosition: function(pos) {
            var subX, subY, map2 = this._map, container = this._container, centerPoint = map2.latLngToContainerPoint(map2.getCenter()), tooltipPoint = map2.layerPointToContainerPoint(pos), direction = this.options.direction, tooltipWidth = container.offsetWidth, tooltipHeight = container.offsetHeight, offset = toPoint(this.options.offset), anchor = this._getAnchor();
            if (direction === "top") {
              subX = tooltipWidth / 2;
              subY = tooltipHeight;
            } else if (direction === "bottom") {
              subX = tooltipWidth / 2;
              subY = 0;
            } else if (direction === "center") {
              subX = tooltipWidth / 2;
              subY = tooltipHeight / 2;
            } else if (direction === "right") {
              subX = 0;
              subY = tooltipHeight / 2;
            } else if (direction === "left") {
              subX = tooltipWidth;
              subY = tooltipHeight / 2;
            } else if (tooltipPoint.x < centerPoint.x) {
              direction = "right";
              subX = 0;
              subY = tooltipHeight / 2;
            } else {
              direction = "left";
              subX = tooltipWidth + (offset.x + anchor.x) * 2;
              subY = tooltipHeight / 2;
            }
            pos = pos.subtract(toPoint(subX, subY, true)).add(offset).add(anchor);
            removeClass(container, "leaflet-tooltip-right");
            removeClass(container, "leaflet-tooltip-left");
            removeClass(container, "leaflet-tooltip-top");
            removeClass(container, "leaflet-tooltip-bottom");
            addClass(container, "leaflet-tooltip-" + direction);
            setPosition(container, pos);
          },
          _updatePosition: function() {
            var pos = this._map.latLngToLayerPoint(this._latlng);
            this._setPosition(pos);
          },
          setOpacity: function(opacity) {
            this.options.opacity = opacity;
            if (this._container) {
              setOpacity(this._container, opacity);
            }
          },
          _animateZoom: function(e) {
            var pos = this._map._latLngToNewLayerPoint(this._latlng, e.zoom, e.center);
            this._setPosition(pos);
          },
          _getAnchor: function() {
            return toPoint(this._source && this._source._getTooltipAnchor && !this.options.sticky ? this._source._getTooltipAnchor() : [0, 0]);
          }
        });
        var tooltip = function(options, source) {
          return new Tooltip(options, source);
        };
        Map3.include({
          // @method openTooltip(tooltip: Tooltip): this
          // Opens the specified tooltip.
          // @alternative
          // @method openTooltip(content: String|HTMLElement, latlng: LatLng, options?: Tooltip options): this
          // Creates a tooltip with the specified content and options and open it.
          openTooltip: function(tooltip2, latlng, options) {
            this._initOverlay(Tooltip, tooltip2, latlng, options).openOn(this);
            return this;
          },
          // @method closeTooltip(tooltip: Tooltip): this
          // Closes the tooltip given as parameter.
          closeTooltip: function(tooltip2) {
            tooltip2.close();
            return this;
          }
        });
        Layer.include({
          // @method bindTooltip(content: String|HTMLElement|Function|Tooltip, options?: Tooltip options): this
          // Binds a tooltip to the layer with the passed `content` and sets up the
          // necessary event listeners. If a `Function` is passed it will receive
          // the layer as the first argument and should return a `String` or `HTMLElement`.
          bindTooltip: function(content, options) {
            if (this._tooltip && this.isTooltipOpen()) {
              this.unbindTooltip();
            }
            this._tooltip = this._initOverlay(Tooltip, this._tooltip, content, options);
            this._initTooltipInteractions();
            if (this._tooltip.options.permanent && this._map && this._map.hasLayer(this)) {
              this.openTooltip();
            }
            return this;
          },
          // @method unbindTooltip(): this
          // Removes the tooltip previously bound with `bindTooltip`.
          unbindTooltip: function() {
            if (this._tooltip) {
              this._initTooltipInteractions(true);
              this.closeTooltip();
              this._tooltip = null;
            }
            return this;
          },
          _initTooltipInteractions: function(remove2) {
            if (!remove2 && this._tooltipHandlersAdded) {
              return;
            }
            var onOff = remove2 ? "off" : "on", events = {
              remove: this.closeTooltip,
              move: this._moveTooltip
            };
            if (!this._tooltip.options.permanent) {
              events.mouseover = this._openTooltip;
              events.mouseout = this.closeTooltip;
              events.click = this._openTooltip;
              if (this._map) {
                this._addFocusListeners();
              } else {
                events.add = this._addFocusListeners;
              }
            } else {
              events.add = this._openTooltip;
            }
            if (this._tooltip.options.sticky) {
              events.mousemove = this._moveTooltip;
            }
            this[onOff](events);
            this._tooltipHandlersAdded = !remove2;
          },
          // @method openTooltip(latlng?: LatLng): this
          // Opens the bound tooltip at the specified `latlng` or at the default tooltip anchor if no `latlng` is passed.
          openTooltip: function(latlng) {
            if (this._tooltip) {
              if (!(this instanceof FeatureGroup)) {
                this._tooltip._source = this;
              }
              if (this._tooltip._prepareOpen(latlng)) {
                this._tooltip.openOn(this._map);
                if (this.getElement) {
                  this._setAriaDescribedByOnLayer(this);
                } else if (this.eachLayer) {
                  this.eachLayer(this._setAriaDescribedByOnLayer, this);
                }
              }
            }
            return this;
          },
          // @method closeTooltip(): this
          // Closes the tooltip bound to this layer if it is open.
          closeTooltip: function() {
            if (this._tooltip) {
              return this._tooltip.close();
            }
          },
          // @method toggleTooltip(): this
          // Opens or closes the tooltip bound to this layer depending on its current state.
          toggleTooltip: function() {
            if (this._tooltip) {
              this._tooltip.toggle(this);
            }
            return this;
          },
          // @method isTooltipOpen(): boolean
          // Returns `true` if the tooltip bound to this layer is currently open.
          isTooltipOpen: function() {
            return this._tooltip.isOpen();
          },
          // @method setTooltipContent(content: String|HTMLElement|Tooltip): this
          // Sets the content of the tooltip bound to this layer.
          setTooltipContent: function(content) {
            if (this._tooltip) {
              this._tooltip.setContent(content);
            }
            return this;
          },
          // @method getTooltip(): Tooltip
          // Returns the tooltip bound to this layer.
          getTooltip: function() {
            return this._tooltip;
          },
          _addFocusListeners: function() {
            if (this.getElement) {
              this._addFocusListenersOnLayer(this);
            } else if (this.eachLayer) {
              this.eachLayer(this._addFocusListenersOnLayer, this);
            }
          },
          _addFocusListenersOnLayer: function(layer) {
            var el = typeof layer.getElement === "function" && layer.getElement();
            if (el) {
              on(el, "focus", function() {
                this._tooltip._source = layer;
                this.openTooltip();
              }, this);
              on(el, "blur", this.closeTooltip, this);
            }
          },
          _setAriaDescribedByOnLayer: function(layer) {
            var el = typeof layer.getElement === "function" && layer.getElement();
            if (el) {
              el.setAttribute("aria-describedby", this._tooltip._container.id);
            }
          },
          _openTooltip: function(e) {
            if (!this._tooltip || !this._map) {
              return;
            }
            if (this._map.dragging && this._map.dragging.moving() && !this._openOnceFlag) {
              this._openOnceFlag = true;
              var that = this;
              this._map.once("moveend", function() {
                that._openOnceFlag = false;
                that._openTooltip(e);
              });
              return;
            }
            this._tooltip._source = e.layer || e.target;
            this.openTooltip(this._tooltip.options.sticky ? e.latlng : void 0);
          },
          _moveTooltip: function(e) {
            var latlng = e.latlng, containerPoint, layerPoint;
            if (this._tooltip.options.sticky && e.originalEvent) {
              containerPoint = this._map.mouseEventToContainerPoint(e.originalEvent);
              layerPoint = this._map.containerPointToLayerPoint(containerPoint);
              latlng = this._map.layerPointToLatLng(layerPoint);
            }
            this._tooltip.setLatLng(latlng);
          }
        });
        var DivIcon = Icon.extend({
          options: {
            // @section
            // @aka DivIcon options
            iconSize: [12, 12],
            // also can be set through CSS
            // iconAnchor: (Point),
            // popupAnchor: (Point),
            // @option html: String|HTMLElement = ''
            // Custom HTML code to put inside the div element, empty by default. Alternatively,
            // an instance of `HTMLElement`.
            html: false,
            // @option bgPos: Point = [0, 0]
            // Optional relative position of the background, in pixels
            bgPos: null,
            className: "leaflet-div-icon"
          },
          createIcon: function(oldIcon) {
            var div = oldIcon && oldIcon.tagName === "DIV" ? oldIcon : document.createElement("div"), options = this.options;
            if (options.html instanceof Element) {
              empty(div);
              div.appendChild(options.html);
            } else {
              div.innerHTML = options.html !== false ? options.html : "";
            }
            if (options.bgPos) {
              var bgPos = toPoint(options.bgPos);
              div.style.backgroundPosition = -bgPos.x + "px " + -bgPos.y + "px";
            }
            this._setIconStyles(div, "icon");
            return div;
          },
          createShadow: function() {
            return null;
          }
        });
        function divIcon(options) {
          return new DivIcon(options);
        }
        Icon.Default = IconDefault;
        var GridLayer = Layer.extend({
          // @section
          // @aka GridLayer options
          options: {
            // @option tileSize: Number|Point = 256
            // Width and height of tiles in the grid. Use a number if width and height are equal, or `L.point(width, height)` otherwise.
            tileSize: 256,
            // @option opacity: Number = 1.0
            // Opacity of the tiles. Can be used in the `createTile()` function.
            opacity: 1,
            // @option updateWhenIdle: Boolean = (depends)
            // Load new tiles only when panning ends.
            // `true` by default on mobile browsers, in order to avoid too many requests and keep smooth navigation.
            // `false` otherwise in order to display new tiles _during_ panning, since it is easy to pan outside the
            // [`keepBuffer`](#gridlayer-keepbuffer) option in desktop browsers.
            updateWhenIdle: Browser.mobile,
            // @option updateWhenZooming: Boolean = true
            // By default, a smooth zoom animation (during a [touch zoom](#map-touchzoom) or a [`flyTo()`](#map-flyto)) will update grid layers every integer zoom level. Setting this option to `false` will update the grid layer only when the smooth animation ends.
            updateWhenZooming: true,
            // @option updateInterval: Number = 200
            // Tiles will not update more than once every `updateInterval` milliseconds when panning.
            updateInterval: 200,
            // @option zIndex: Number = 1
            // The explicit zIndex of the tile layer.
            zIndex: 1,
            // @option bounds: LatLngBounds = undefined
            // If set, tiles will only be loaded inside the set `LatLngBounds`.
            bounds: null,
            // @option minZoom: Number = 0
            // The minimum zoom level down to which this layer will be displayed (inclusive).
            minZoom: 0,
            // @option maxZoom: Number = undefined
            // The maximum zoom level up to which this layer will be displayed (inclusive).
            maxZoom: void 0,
            // @option maxNativeZoom: Number = undefined
            // Maximum zoom number the tile source has available. If it is specified,
            // the tiles on all zoom levels higher than `maxNativeZoom` will be loaded
            // from `maxNativeZoom` level and auto-scaled.
            maxNativeZoom: void 0,
            // @option minNativeZoom: Number = undefined
            // Minimum zoom number the tile source has available. If it is specified,
            // the tiles on all zoom levels lower than `minNativeZoom` will be loaded
            // from `minNativeZoom` level and auto-scaled.
            minNativeZoom: void 0,
            // @option noWrap: Boolean = false
            // Whether the layer is wrapped around the antimeridian. If `true`, the
            // GridLayer will only be displayed once at low zoom levels. Has no
            // effect when the [map CRS](#map-crs) doesn't wrap around. Can be used
            // in combination with [`bounds`](#gridlayer-bounds) to prevent requesting
            // tiles outside the CRS limits.
            noWrap: false,
            // @option pane: String = 'tilePane'
            // `Map pane` where the grid layer will be added.
            pane: "tilePane",
            // @option className: String = ''
            // A custom class name to assign to the tile layer. Empty by default.
            className: "",
            // @option keepBuffer: Number = 2
            // When panning the map, keep this many rows and columns of tiles before unloading them.
            keepBuffer: 2
          },
          initialize: function(options) {
            setOptions(this, options);
          },
          onAdd: function() {
            this._initContainer();
            this._levels = {};
            this._tiles = {};
            this._resetView();
          },
          beforeAdd: function(map2) {
            map2._addZoomLimit(this);
          },
          onRemove: function(map2) {
            this._removeAllTiles();
            remove(this._container);
            map2._removeZoomLimit(this);
            this._container = null;
            this._tileZoom = void 0;
          },
          // @method bringToFront: this
          // Brings the tile layer to the top of all tile layers.
          bringToFront: function() {
            if (this._map) {
              toFront(this._container);
              this._setAutoZIndex(Math.max);
            }
            return this;
          },
          // @method bringToBack: this
          // Brings the tile layer to the bottom of all tile layers.
          bringToBack: function() {
            if (this._map) {
              toBack(this._container);
              this._setAutoZIndex(Math.min);
            }
            return this;
          },
          // @method getContainer: HTMLElement
          // Returns the HTML element that contains the tiles for this layer.
          getContainer: function() {
            return this._container;
          },
          // @method setOpacity(opacity: Number): this
          // Changes the [opacity](#gridlayer-opacity) of the grid layer.
          setOpacity: function(opacity) {
            this.options.opacity = opacity;
            this._updateOpacity();
            return this;
          },
          // @method setZIndex(zIndex: Number): this
          // Changes the [zIndex](#gridlayer-zindex) of the grid layer.
          setZIndex: function(zIndex) {
            this.options.zIndex = zIndex;
            this._updateZIndex();
            return this;
          },
          // @method isLoading: Boolean
          // Returns `true` if any tile in the grid layer has not finished loading.
          isLoading: function() {
            return this._loading;
          },
          // @method redraw: this
          // Causes the layer to clear all the tiles and request them again.
          redraw: function() {
            if (this._map) {
              this._removeAllTiles();
              var tileZoom = this._clampZoom(this._map.getZoom());
              if (tileZoom !== this._tileZoom) {
                this._tileZoom = tileZoom;
                this._updateLevels();
              }
              this._update();
            }
            return this;
          },
          getEvents: function() {
            var events = {
              viewprereset: this._invalidateAll,
              viewreset: this._resetView,
              zoom: this._resetView,
              moveend: this._onMoveEnd
            };
            if (!this.options.updateWhenIdle) {
              if (!this._onMove) {
                this._onMove = throttle(this._onMoveEnd, this.options.updateInterval, this);
              }
              events.move = this._onMove;
            }
            if (this._zoomAnimated) {
              events.zoomanim = this._animateZoom;
            }
            return events;
          },
          // @section Extension methods
          // Layers extending `GridLayer` shall reimplement the following method.
          // @method createTile(coords: Object, done?: Function): HTMLElement
          // Called only internally, must be overridden by classes extending `GridLayer`.
          // Returns the `HTMLElement` corresponding to the given `coords`. If the `done` callback
          // is specified, it must be called when the tile has finished loading and drawing.
          createTile: function() {
            return document.createElement("div");
          },
          // @section
          // @method getTileSize: Point
          // Normalizes the [tileSize option](#gridlayer-tilesize) into a point. Used by the `createTile()` method.
          getTileSize: function() {
            var s = this.options.tileSize;
            return s instanceof Point ? s : new Point(s, s);
          },
          _updateZIndex: function() {
            if (this._container && this.options.zIndex !== void 0 && this.options.zIndex !== null) {
              this._container.style.zIndex = this.options.zIndex;
            }
          },
          _setAutoZIndex: function(compare) {
            var layers2 = this.getPane().children, edgeZIndex = -compare(-Infinity, Infinity);
            for (var i = 0, len = layers2.length, zIndex; i < len; i++) {
              zIndex = layers2[i].style.zIndex;
              if (layers2[i] !== this._container && zIndex) {
                edgeZIndex = compare(edgeZIndex, +zIndex);
              }
            }
            if (isFinite(edgeZIndex)) {
              this.options.zIndex = edgeZIndex + compare(-1, 1);
              this._updateZIndex();
            }
          },
          _updateOpacity: function() {
            if (!this._map) {
              return;
            }
            if (Browser.ielt9) {
              return;
            }
            setOpacity(this._container, this.options.opacity);
            var now = +/* @__PURE__ */ new Date(), nextFrame = false, willPrune = false;
            for (var key in this._tiles) {
              var tile = this._tiles[key];
              if (!tile.current || !tile.loaded) {
                continue;
              }
              var fade = Math.min(1, (now - tile.loaded) / 200);
              setOpacity(tile.el, fade);
              if (fade < 1) {
                nextFrame = true;
              } else {
                if (tile.active) {
                  willPrune = true;
                } else {
                  this._onOpaqueTile(tile);
                }
                tile.active = true;
              }
            }
            if (willPrune && !this._noPrune) {
              this._pruneTiles();
            }
            if (nextFrame) {
              cancelAnimFrame(this._fadeFrame);
              this._fadeFrame = requestAnimFrame(this._updateOpacity, this);
            }
          },
          _onOpaqueTile: falseFn,
          _initContainer: function() {
            if (this._container) {
              return;
            }
            this._container = create$1("div", "leaflet-layer " + (this.options.className || ""));
            this._updateZIndex();
            if (this.options.opacity < 1) {
              this._updateOpacity();
            }
            this.getPane().appendChild(this._container);
          },
          _updateLevels: function() {
            var zoom2 = this._tileZoom, maxZoom = this.options.maxZoom;
            if (zoom2 === void 0) {
              return void 0;
            }
            for (var z in this._levels) {
              z = Number(z);
              if (this._levels[z].el.children.length || z === zoom2) {
                this._levels[z].el.style.zIndex = maxZoom - Math.abs(zoom2 - z);
                this._onUpdateLevel(z);
              } else {
                remove(this._levels[z].el);
                this._removeTilesAtZoom(z);
                this._onRemoveLevel(z);
                delete this._levels[z];
              }
            }
            var level = this._levels[zoom2], map2 = this._map;
            if (!level) {
              level = this._levels[zoom2] = {};
              level.el = create$1("div", "leaflet-tile-container leaflet-zoom-animated", this._container);
              level.el.style.zIndex = maxZoom;
              level.origin = map2.project(map2.unproject(map2.getPixelOrigin()), zoom2).round();
              level.zoom = zoom2;
              this._setZoomTransform(level, map2.getCenter(), map2.getZoom());
              falseFn(level.el.offsetWidth);
              this._onCreateLevel(level);
            }
            this._level = level;
            return level;
          },
          _onUpdateLevel: falseFn,
          _onRemoveLevel: falseFn,
          _onCreateLevel: falseFn,
          _pruneTiles: function() {
            if (!this._map) {
              return;
            }
            var key, tile;
            var zoom2 = this._map.getZoom();
            if (zoom2 > this.options.maxZoom || zoom2 < this.options.minZoom) {
              this._removeAllTiles();
              return;
            }
            for (key in this._tiles) {
              tile = this._tiles[key];
              tile.retain = tile.current;
            }
            for (key in this._tiles) {
              tile = this._tiles[key];
              if (tile.current && !tile.active) {
                var coords = tile.coords;
                if (!this._retainParent(coords.x, coords.y, coords.z, coords.z - 5)) {
                  this._retainChildren(coords.x, coords.y, coords.z, coords.z + 2);
                }
              }
            }
            for (key in this._tiles) {
              if (!this._tiles[key].retain) {
                this._removeTile(key);
              }
            }
          },
          _removeTilesAtZoom: function(zoom2) {
            for (var key in this._tiles) {
              if (this._tiles[key].coords.z !== zoom2) {
                continue;
              }
              this._removeTile(key);
            }
          },
          _removeAllTiles: function() {
            for (var key in this._tiles) {
              this._removeTile(key);
            }
          },
          _invalidateAll: function() {
            for (var z in this._levels) {
              remove(this._levels[z].el);
              this._onRemoveLevel(Number(z));
              delete this._levels[z];
            }
            this._removeAllTiles();
            this._tileZoom = void 0;
          },
          _retainParent: function(x, y, z, minZoom) {
            var x2 = Math.floor(x / 2), y2 = Math.floor(y / 2), z2 = z - 1, coords2 = new Point(+x2, +y2);
            coords2.z = +z2;
            var key = this._tileCoordsToKey(coords2), tile = this._tiles[key];
            if (tile && tile.active) {
              tile.retain = true;
              return true;
            } else if (tile && tile.loaded) {
              tile.retain = true;
            }
            if (z2 > minZoom) {
              return this._retainParent(x2, y2, z2, minZoom);
            }
            return false;
          },
          _retainChildren: function(x, y, z, maxZoom) {
            for (var i = 2 * x; i < 2 * x + 2; i++) {
              for (var j = 2 * y; j < 2 * y + 2; j++) {
                var coords = new Point(i, j);
                coords.z = z + 1;
                var key = this._tileCoordsToKey(coords), tile = this._tiles[key];
                if (tile && tile.active) {
                  tile.retain = true;
                  continue;
                } else if (tile && tile.loaded) {
                  tile.retain = true;
                }
                if (z + 1 < maxZoom) {
                  this._retainChildren(i, j, z + 1, maxZoom);
                }
              }
            }
          },
          _resetView: function(e) {
            var animating = e && (e.pinch || e.flyTo);
            this._setView(this._map.getCenter(), this._map.getZoom(), animating, animating);
          },
          _animateZoom: function(e) {
            this._setView(e.center, e.zoom, true, e.noUpdate);
          },
          _clampZoom: function(zoom2) {
            var options = this.options;
            if (void 0 !== options.minNativeZoom && zoom2 < options.minNativeZoom) {
              return options.minNativeZoom;
            }
            if (void 0 !== options.maxNativeZoom && options.maxNativeZoom < zoom2) {
              return options.maxNativeZoom;
            }
            return zoom2;
          },
          _setView: function(center, zoom2, noPrune, noUpdate) {
            var tileZoom = Math.round(zoom2);
            if (this.options.maxZoom !== void 0 && tileZoom > this.options.maxZoom || this.options.minZoom !== void 0 && tileZoom < this.options.minZoom) {
              tileZoom = void 0;
            } else {
              tileZoom = this._clampZoom(tileZoom);
            }
            var tileZoomChanged = this.options.updateWhenZooming && tileZoom !== this._tileZoom;
            if (!noUpdate || tileZoomChanged) {
              this._tileZoom = tileZoom;
              if (this._abortLoading) {
                this._abortLoading();
              }
              this._updateLevels();
              this._resetGrid();
              if (tileZoom !== void 0) {
                this._update(center);
              }
              if (!noPrune) {
                this._pruneTiles();
              }
              this._noPrune = !!noPrune;
            }
            this._setZoomTransforms(center, zoom2);
          },
          _setZoomTransforms: function(center, zoom2) {
            for (var i in this._levels) {
              this._setZoomTransform(this._levels[i], center, zoom2);
            }
          },
          _setZoomTransform: function(level, center, zoom2) {
            var scale2 = this._map.getZoomScale(zoom2, level.zoom), translate = level.origin.multiplyBy(scale2).subtract(this._map._getNewPixelOrigin(center, zoom2)).round();
            if (Browser.any3d) {
              setTransform(level.el, translate, scale2);
            } else {
              setPosition(level.el, translate);
            }
          },
          _resetGrid: function() {
            var map2 = this._map, crs = map2.options.crs, tileSize = this._tileSize = this.getTileSize(), tileZoom = this._tileZoom;
            var bounds = this._map.getPixelWorldBounds(this._tileZoom);
            if (bounds) {
              this._globalTileRange = this._pxBoundsToTileRange(bounds);
            }
            this._wrapX = crs.wrapLng && !this.options.noWrap && [
              Math.floor(map2.project([0, crs.wrapLng[0]], tileZoom).x / tileSize.x),
              Math.ceil(map2.project([0, crs.wrapLng[1]], tileZoom).x / tileSize.y)
            ];
            this._wrapY = crs.wrapLat && !this.options.noWrap && [
              Math.floor(map2.project([crs.wrapLat[0], 0], tileZoom).y / tileSize.x),
              Math.ceil(map2.project([crs.wrapLat[1], 0], tileZoom).y / tileSize.y)
            ];
          },
          _onMoveEnd: function() {
            if (!this._map || this._map._animatingZoom) {
              return;
            }
            this._update();
          },
          _getTiledPixelBounds: function(center) {
            var map2 = this._map, mapZoom = map2._animatingZoom ? Math.max(map2._animateToZoom, map2.getZoom()) : map2.getZoom(), scale2 = map2.getZoomScale(mapZoom, this._tileZoom), pixelCenter = map2.project(center, this._tileZoom).floor(), halfSize = map2.getSize().divideBy(scale2 * 2);
            return new Bounds(pixelCenter.subtract(halfSize), pixelCenter.add(halfSize));
          },
          // Private method to load tiles in the grid's active zoom level according to map bounds
          _update: function(center) {
            var map2 = this._map;
            if (!map2) {
              return;
            }
            var zoom2 = this._clampZoom(map2.getZoom());
            if (center === void 0) {
              center = map2.getCenter();
            }
            if (this._tileZoom === void 0) {
              return;
            }
            var pixelBounds = this._getTiledPixelBounds(center), tileRange = this._pxBoundsToTileRange(pixelBounds), tileCenter = tileRange.getCenter(), queue = [], margin = this.options.keepBuffer, noPruneRange = new Bounds(
              tileRange.getBottomLeft().subtract([margin, -margin]),
              tileRange.getTopRight().add([margin, -margin])
            );
            if (!(isFinite(tileRange.min.x) && isFinite(tileRange.min.y) && isFinite(tileRange.max.x) && isFinite(tileRange.max.y))) {
              throw new Error("Attempted to load an infinite number of tiles");
            }
            for (var key in this._tiles) {
              var c = this._tiles[key].coords;
              if (c.z !== this._tileZoom || !noPruneRange.contains(new Point(c.x, c.y))) {
                this._tiles[key].current = false;
              }
            }
            if (Math.abs(zoom2 - this._tileZoom) > 1) {
              this._setView(center, zoom2);
              return;
            }
            for (var j = tileRange.min.y; j <= tileRange.max.y; j++) {
              for (var i = tileRange.min.x; i <= tileRange.max.x; i++) {
                var coords = new Point(i, j);
                coords.z = this._tileZoom;
                if (!this._isValidTile(coords)) {
                  continue;
                }
                var tile = this._tiles[this._tileCoordsToKey(coords)];
                if (tile) {
                  tile.current = true;
                } else {
                  queue.push(coords);
                }
              }
            }
            queue.sort(function(a, b) {
              return a.distanceTo(tileCenter) - b.distanceTo(tileCenter);
            });
            if (queue.length !== 0) {
              if (!this._loading) {
                this._loading = true;
                this.fire("loading");
              }
              var fragment = document.createDocumentFragment();
              for (i = 0; i < queue.length; i++) {
                this._addTile(queue[i], fragment);
              }
              this._level.el.appendChild(fragment);
            }
          },
          _isValidTile: function(coords) {
            var crs = this._map.options.crs;
            if (!crs.infinite) {
              var bounds = this._globalTileRange;
              if (!crs.wrapLng && (coords.x < bounds.min.x || coords.x > bounds.max.x) || !crs.wrapLat && (coords.y < bounds.min.y || coords.y > bounds.max.y)) {
                return false;
              }
            }
            if (!this.options.bounds) {
              return true;
            }
            var tileBounds = this._tileCoordsToBounds(coords);
            return toLatLngBounds(this.options.bounds).overlaps(tileBounds);
          },
          _keyToBounds: function(key) {
            return this._tileCoordsToBounds(this._keyToTileCoords(key));
          },
          _tileCoordsToNwSe: function(coords) {
            var map2 = this._map, tileSize = this.getTileSize(), nwPoint = coords.scaleBy(tileSize), sePoint = nwPoint.add(tileSize), nw = map2.unproject(nwPoint, coords.z), se = map2.unproject(sePoint, coords.z);
            return [nw, se];
          },
          // converts tile coordinates to its geographical bounds
          _tileCoordsToBounds: function(coords) {
            var bp = this._tileCoordsToNwSe(coords), bounds = new LatLngBounds(bp[0], bp[1]);
            if (!this.options.noWrap) {
              bounds = this._map.wrapLatLngBounds(bounds);
            }
            return bounds;
          },
          // converts tile coordinates to key for the tile cache
          _tileCoordsToKey: function(coords) {
            return coords.x + ":" + coords.y + ":" + coords.z;
          },
          // converts tile cache key to coordinates
          _keyToTileCoords: function(key) {
            var k = key.split(":"), coords = new Point(+k[0], +k[1]);
            coords.z = +k[2];
            return coords;
          },
          _removeTile: function(key) {
            var tile = this._tiles[key];
            if (!tile) {
              return;
            }
            remove(tile.el);
            delete this._tiles[key];
            this.fire("tileunload", {
              tile: tile.el,
              coords: this._keyToTileCoords(key)
            });
          },
          _initTile: function(tile) {
            addClass(tile, "leaflet-tile");
            var tileSize = this.getTileSize();
            tile.style.width = tileSize.x + "px";
            tile.style.height = tileSize.y + "px";
            tile.onselectstart = falseFn;
            tile.onmousemove = falseFn;
            if (Browser.ielt9 && this.options.opacity < 1) {
              setOpacity(tile, this.options.opacity);
            }
          },
          _addTile: function(coords, container) {
            var tilePos = this._getTilePos(coords), key = this._tileCoordsToKey(coords);
            var tile = this.createTile(this._wrapCoords(coords), bind(this._tileReady, this, coords));
            this._initTile(tile);
            if (this.createTile.length < 2) {
              requestAnimFrame(bind(this._tileReady, this, coords, null, tile));
            }
            setPosition(tile, tilePos);
            this._tiles[key] = {
              el: tile,
              coords,
              current: true
            };
            container.appendChild(tile);
            this.fire("tileloadstart", {
              tile,
              coords
            });
          },
          _tileReady: function(coords, err, tile) {
            if (err) {
              this.fire("tileerror", {
                error: err,
                tile,
                coords
              });
            }
            var key = this._tileCoordsToKey(coords);
            tile = this._tiles[key];
            if (!tile) {
              return;
            }
            tile.loaded = +/* @__PURE__ */ new Date();
            if (this._map._fadeAnimated) {
              setOpacity(tile.el, 0);
              cancelAnimFrame(this._fadeFrame);
              this._fadeFrame = requestAnimFrame(this._updateOpacity, this);
            } else {
              tile.active = true;
              this._pruneTiles();
            }
            if (!err) {
              addClass(tile.el, "leaflet-tile-loaded");
              this.fire("tileload", {
                tile: tile.el,
                coords
              });
            }
            if (this._noTilesToLoad()) {
              this._loading = false;
              this.fire("load");
              if (Browser.ielt9 || !this._map._fadeAnimated) {
                requestAnimFrame(this._pruneTiles, this);
              } else {
                setTimeout(bind(this._pruneTiles, this), 250);
              }
            }
          },
          _getTilePos: function(coords) {
            return coords.scaleBy(this.getTileSize()).subtract(this._level.origin);
          },
          _wrapCoords: function(coords) {
            var newCoords = new Point(
              this._wrapX ? wrapNum(coords.x, this._wrapX) : coords.x,
              this._wrapY ? wrapNum(coords.y, this._wrapY) : coords.y
            );
            newCoords.z = coords.z;
            return newCoords;
          },
          _pxBoundsToTileRange: function(bounds) {
            var tileSize = this.getTileSize();
            return new Bounds(
              bounds.min.unscaleBy(tileSize).floor(),
              bounds.max.unscaleBy(tileSize).ceil().subtract([1, 1])
            );
          },
          _noTilesToLoad: function() {
            for (var key in this._tiles) {
              if (!this._tiles[key].loaded) {
                return false;
              }
            }
            return true;
          }
        });
        function gridLayer(options) {
          return new GridLayer(options);
        }
        var TileLayer = GridLayer.extend({
          // @section
          // @aka TileLayer options
          options: {
            // @option minZoom: Number = 0
            // The minimum zoom level down to which this layer will be displayed (inclusive).
            minZoom: 0,
            // @option maxZoom: Number = 18
            // The maximum zoom level up to which this layer will be displayed (inclusive).
            maxZoom: 18,
            // @option subdomains: String|String[] = 'abc'
            // Subdomains of the tile service. Can be passed in the form of one string (where each letter is a subdomain name) or an array of strings.
            subdomains: "abc",
            // @option errorTileUrl: String = ''
            // URL to the tile image to show in place of the tile that failed to load.
            errorTileUrl: "",
            // @option zoomOffset: Number = 0
            // The zoom number used in tile URLs will be offset with this value.
            zoomOffset: 0,
            // @option tms: Boolean = false
            // If `true`, inverses Y axis numbering for tiles (turn this on for [TMS](https://en.wikipedia.org/wiki/Tile_Map_Service) services).
            tms: false,
            // @option zoomReverse: Boolean = false
            // If set to true, the zoom number used in tile URLs will be reversed (`maxZoom - zoom` instead of `zoom`)
            zoomReverse: false,
            // @option detectRetina: Boolean = false
            // If `true` and user is on a retina display, it will request four tiles of half the specified size and a bigger zoom level in place of one to utilize the high resolution.
            detectRetina: false,
            // @option crossOrigin: Boolean|String = false
            // Whether the crossOrigin attribute will be added to the tiles.
            // If a String is provided, all tiles will have their crossOrigin attribute set to the String provided. This is needed if you want to access tile pixel data.
            // Refer to [CORS Settings](https://developer.mozilla.org/en-US/docs/Web/HTML/CORS_settings_attributes) for valid String values.
            crossOrigin: false,
            // @option referrerPolicy: Boolean|String = false
            // Whether the referrerPolicy attribute will be added to the tiles.
            // If a String is provided, all tiles will have their referrerPolicy attribute set to the String provided.
            // This may be needed if your map's rendering context has a strict default but your tile provider expects a valid referrer
            // (e.g. to validate an API token).
            // Refer to [HTMLImageElement.referrerPolicy](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/referrerPolicy) for valid String values.
            referrerPolicy: false
          },
          initialize: function(url, options) {
            this._url = url;
            options = setOptions(this, options);
            if (options.detectRetina && Browser.retina && options.maxZoom > 0) {
              options.tileSize = Math.floor(options.tileSize / 2);
              if (!options.zoomReverse) {
                options.zoomOffset++;
                options.maxZoom = Math.max(options.minZoom, options.maxZoom - 1);
              } else {
                options.zoomOffset--;
                options.minZoom = Math.min(options.maxZoom, options.minZoom + 1);
              }
              options.minZoom = Math.max(0, options.minZoom);
            } else if (!options.zoomReverse) {
              options.maxZoom = Math.max(options.minZoom, options.maxZoom);
            } else {
              options.minZoom = Math.min(options.maxZoom, options.minZoom);
            }
            if (typeof options.subdomains === "string") {
              options.subdomains = options.subdomains.split("");
            }
            this.on("tileunload", this._onTileRemove);
          },
          // @method setUrl(url: String, noRedraw?: Boolean): this
          // Updates the layer's URL template and redraws it (unless `noRedraw` is set to `true`).
          // If the URL does not change, the layer will not be redrawn unless
          // the noRedraw parameter is set to false.
          setUrl: function(url, noRedraw) {
            if (this._url === url && noRedraw === void 0) {
              noRedraw = true;
            }
            this._url = url;
            if (!noRedraw) {
              this.redraw();
            }
            return this;
          },
          // @method createTile(coords: Object, done?: Function): HTMLElement
          // Called only internally, overrides GridLayer's [`createTile()`](#gridlayer-createtile)
          // to return an `<img>` HTML element with the appropriate image URL given `coords`. The `done`
          // callback is called when the tile has been loaded.
          createTile: function(coords, done) {
            var tile = document.createElement("img");
            on(tile, "load", bind(this._tileOnLoad, this, done, tile));
            on(tile, "error", bind(this._tileOnError, this, done, tile));
            if (this.options.crossOrigin || this.options.crossOrigin === "") {
              tile.crossOrigin = this.options.crossOrigin === true ? "" : this.options.crossOrigin;
            }
            if (typeof this.options.referrerPolicy === "string") {
              tile.referrerPolicy = this.options.referrerPolicy;
            }
            tile.alt = "";
            tile.src = this.getTileUrl(coords);
            return tile;
          },
          // @section Extension methods
          // @uninheritable
          // Layers extending `TileLayer` might reimplement the following method.
          // @method getTileUrl(coords: Object): String
          // Called only internally, returns the URL for a tile given its coordinates.
          // Classes extending `TileLayer` can override this function to provide custom tile URL naming schemes.
          getTileUrl: function(coords) {
            var data = {
              r: Browser.retina ? "@2x" : "",
              s: this._getSubdomain(coords),
              x: coords.x,
              y: coords.y,
              z: this._getZoomForUrl()
            };
            if (this._map && !this._map.options.crs.infinite) {
              var invertedY = this._globalTileRange.max.y - coords.y;
              if (this.options.tms) {
                data["y"] = invertedY;
              }
              data["-y"] = invertedY;
            }
            return template(this._url, extend(data, this.options));
          },
          _tileOnLoad: function(done, tile) {
            if (Browser.ielt9) {
              setTimeout(bind(done, this, null, tile), 0);
            } else {
              done(null, tile);
            }
          },
          _tileOnError: function(done, tile, e) {
            var errorUrl = this.options.errorTileUrl;
            if (errorUrl && tile.getAttribute("src") !== errorUrl) {
              tile.src = errorUrl;
            }
            done(e, tile);
          },
          _onTileRemove: function(e) {
            e.tile.onload = null;
          },
          _getZoomForUrl: function() {
            var zoom2 = this._tileZoom, maxZoom = this.options.maxZoom, zoomReverse = this.options.zoomReverse, zoomOffset = this.options.zoomOffset;
            if (zoomReverse) {
              zoom2 = maxZoom - zoom2;
            }
            return zoom2 + zoomOffset;
          },
          _getSubdomain: function(tilePoint) {
            var index2 = Math.abs(tilePoint.x + tilePoint.y) % this.options.subdomains.length;
            return this.options.subdomains[index2];
          },
          // stops loading all tiles in the background layer
          _abortLoading: function() {
            var i, tile;
            for (i in this._tiles) {
              if (this._tiles[i].coords.z !== this._tileZoom) {
                tile = this._tiles[i].el;
                tile.onload = falseFn;
                tile.onerror = falseFn;
                if (!tile.complete) {
                  tile.src = emptyImageUrl;
                  var coords = this._tiles[i].coords;
                  remove(tile);
                  delete this._tiles[i];
                  this.fire("tileabort", {
                    tile,
                    coords
                  });
                }
              }
            }
          },
          _removeTile: function(key) {
            var tile = this._tiles[key];
            if (!tile) {
              return;
            }
            tile.el.setAttribute("src", emptyImageUrl);
            return GridLayer.prototype._removeTile.call(this, key);
          },
          _tileReady: function(coords, err, tile) {
            if (!this._map || tile && tile.getAttribute("src") === emptyImageUrl) {
              return;
            }
            return GridLayer.prototype._tileReady.call(this, coords, err, tile);
          }
        });
        function tileLayer(url, options) {
          return new TileLayer(url, options);
        }
        var TileLayerWMS = TileLayer.extend({
          // @section
          // @aka TileLayer.WMS options
          // If any custom options not documented here are used, they will be sent to the
          // WMS server as extra parameters in each request URL. This can be useful for
          // [non-standard vendor WMS parameters](https://docs.geoserver.org/stable/en/user/services/wms/vendor.html).
          defaultWmsParams: {
            service: "WMS",
            request: "GetMap",
            // @option layers: String = ''
            // **(required)** Comma-separated list of WMS layers to show.
            layers: "",
            // @option styles: String = ''
            // Comma-separated list of WMS styles.
            styles: "",
            // @option format: String = 'image/jpeg'
            // WMS image format (use `'image/png'` for layers with transparency).
            format: "image/jpeg",
            // @option transparent: Boolean = false
            // If `true`, the WMS service will return images with transparency.
            transparent: false,
            // @option version: String = '1.1.1'
            // Version of the WMS service to use
            version: "1.1.1"
          },
          options: {
            // @option crs: CRS = null
            // Coordinate Reference System to use for the WMS requests, defaults to
            // map CRS. Don't change this if you're not sure what it means.
            crs: null,
            // @option uppercase: Boolean = false
            // If `true`, WMS request parameter keys will be uppercase.
            uppercase: false
          },
          initialize: function(url, options) {
            this._url = url;
            var wmsParams = extend({}, this.defaultWmsParams);
            for (var i in options) {
              if (!(i in this.options)) {
                wmsParams[i] = options[i];
              }
            }
            options = setOptions(this, options);
            var realRetina = options.detectRetina && Browser.retina ? 2 : 1;
            var tileSize = this.getTileSize();
            wmsParams.width = tileSize.x * realRetina;
            wmsParams.height = tileSize.y * realRetina;
            this.wmsParams = wmsParams;
          },
          onAdd: function(map2) {
            this._crs = this.options.crs || map2.options.crs;
            this._wmsVersion = parseFloat(this.wmsParams.version);
            var projectionKey = this._wmsVersion >= 1.3 ? "crs" : "srs";
            this.wmsParams[projectionKey] = this._crs.code;
            TileLayer.prototype.onAdd.call(this, map2);
          },
          getTileUrl: function(coords) {
            var tileBounds = this._tileCoordsToNwSe(coords), crs = this._crs, bounds = toBounds(crs.project(tileBounds[0]), crs.project(tileBounds[1])), min = bounds.min, max = bounds.max, bbox = (this._wmsVersion >= 1.3 && this._crs === EPSG4326 ? [min.y, min.x, max.y, max.x] : [min.x, min.y, max.x, max.y]).join(","), url = TileLayer.prototype.getTileUrl.call(this, coords);
            return url + getParamString(this.wmsParams, url, this.options.uppercase) + (this.options.uppercase ? "&BBOX=" : "&bbox=") + bbox;
          },
          // @method setParams(params: Object, noRedraw?: Boolean): this
          // Merges an object with the new parameters and re-requests tiles on the current screen (unless `noRedraw` was set to true).
          setParams: function(params, noRedraw) {
            extend(this.wmsParams, params);
            if (!noRedraw) {
              this.redraw();
            }
            return this;
          }
        });
        function tileLayerWMS(url, options) {
          return new TileLayerWMS(url, options);
        }
        TileLayer.WMS = TileLayerWMS;
        tileLayer.wms = tileLayerWMS;
        var Renderer = Layer.extend({
          // @section
          // @aka Renderer options
          options: {
            // @option padding: Number = 0.1
            // How much to extend the clip area around the map view (relative to its size)
            // e.g. 0.1 would be 10% of map view in each direction
            padding: 0.1
          },
          initialize: function(options) {
            setOptions(this, options);
            stamp(this);
            this._layers = this._layers || {};
          },
          onAdd: function() {
            if (!this._container) {
              this._initContainer();
              addClass(this._container, "leaflet-zoom-animated");
            }
            this.getPane().appendChild(this._container);
            this._update();
            this.on("update", this._updatePaths, this);
          },
          onRemove: function() {
            this.off("update", this._updatePaths, this);
            this._destroyContainer();
          },
          getEvents: function() {
            var events = {
              viewreset: this._reset,
              zoom: this._onZoom,
              moveend: this._update,
              zoomend: this._onZoomEnd
            };
            if (this._zoomAnimated) {
              events.zoomanim = this._onAnimZoom;
            }
            return events;
          },
          _onAnimZoom: function(ev) {
            this._updateTransform(ev.center, ev.zoom);
          },
          _onZoom: function() {
            this._updateTransform(this._map.getCenter(), this._map.getZoom());
          },
          _updateTransform: function(center, zoom2) {
            var scale2 = this._map.getZoomScale(zoom2, this._zoom), viewHalf = this._map.getSize().multiplyBy(0.5 + this.options.padding), currentCenterPoint = this._map.project(this._center, zoom2), topLeftOffset = viewHalf.multiplyBy(-scale2).add(currentCenterPoint).subtract(this._map._getNewPixelOrigin(center, zoom2));
            if (Browser.any3d) {
              setTransform(this._container, topLeftOffset, scale2);
            } else {
              setPosition(this._container, topLeftOffset);
            }
          },
          _reset: function() {
            this._update();
            this._updateTransform(this._center, this._zoom);
            for (var id in this._layers) {
              this._layers[id]._reset();
            }
          },
          _onZoomEnd: function() {
            for (var id in this._layers) {
              this._layers[id]._project();
            }
          },
          _updatePaths: function() {
            for (var id in this._layers) {
              this._layers[id]._update();
            }
          },
          _update: function() {
            var p = this.options.padding, size = this._map.getSize(), min = this._map.containerPointToLayerPoint(size.multiplyBy(-p)).round();
            this._bounds = new Bounds(min, min.add(size.multiplyBy(1 + p * 2)).round());
            this._center = this._map.getCenter();
            this._zoom = this._map.getZoom();
          }
        });
        var Canvas = Renderer.extend({
          // @section
          // @aka Canvas options
          options: {
            // @option tolerance: Number = 0
            // How much to extend the click tolerance around a path/object on the map.
            tolerance: 0
          },
          getEvents: function() {
            var events = Renderer.prototype.getEvents.call(this);
            events.viewprereset = this._onViewPreReset;
            return events;
          },
          _onViewPreReset: function() {
            this._postponeUpdatePaths = true;
          },
          onAdd: function() {
            Renderer.prototype.onAdd.call(this);
            this._draw();
          },
          _initContainer: function() {
            var container = this._container = document.createElement("canvas");
            on(container, "mousemove", this._onMouseMove, this);
            on(container, "click dblclick mousedown mouseup contextmenu", this._onClick, this);
            on(container, "mouseout", this._handleMouseOut, this);
            container["_leaflet_disable_events"] = true;
            this._ctx = container.getContext("2d");
          },
          _destroyContainer: function() {
            cancelAnimFrame(this._redrawRequest);
            delete this._ctx;
            remove(this._container);
            off(this._container);
            delete this._container;
          },
          _updatePaths: function() {
            if (this._postponeUpdatePaths) {
              return;
            }
            var layer;
            this._redrawBounds = null;
            for (var id in this._layers) {
              layer = this._layers[id];
              layer._update();
            }
            this._redraw();
          },
          _update: function() {
            if (this._map._animatingZoom && this._bounds) {
              return;
            }
            Renderer.prototype._update.call(this);
            var b = this._bounds, container = this._container, size = b.getSize(), m = Browser.retina ? 2 : 1;
            setPosition(container, b.min);
            container.width = m * size.x;
            container.height = m * size.y;
            container.style.width = size.x + "px";
            container.style.height = size.y + "px";
            if (Browser.retina) {
              this._ctx.scale(2, 2);
            }
            this._ctx.translate(-b.min.x, -b.min.y);
            this.fire("update");
          },
          _reset: function() {
            Renderer.prototype._reset.call(this);
            if (this._postponeUpdatePaths) {
              this._postponeUpdatePaths = false;
              this._updatePaths();
            }
          },
          _initPath: function(layer) {
            this._updateDashArray(layer);
            this._layers[stamp(layer)] = layer;
            var order = layer._order = {
              layer,
              prev: this._drawLast,
              next: null
            };
            if (this._drawLast) {
              this._drawLast.next = order;
            }
            this._drawLast = order;
            this._drawFirst = this._drawFirst || this._drawLast;
          },
          _addPath: function(layer) {
            this._requestRedraw(layer);
          },
          _removePath: function(layer) {
            var order = layer._order;
            var next = order.next;
            var prev = order.prev;
            if (next) {
              next.prev = prev;
            } else {
              this._drawLast = prev;
            }
            if (prev) {
              prev.next = next;
            } else {
              this._drawFirst = next;
            }
            delete layer._order;
            delete this._layers[stamp(layer)];
            this._requestRedraw(layer);
          },
          _updatePath: function(layer) {
            this._extendRedrawBounds(layer);
            layer._project();
            layer._update();
            this._requestRedraw(layer);
          },
          _updateStyle: function(layer) {
            this._updateDashArray(layer);
            this._requestRedraw(layer);
          },
          _updateDashArray: function(layer) {
            if (typeof layer.options.dashArray === "string") {
              var parts = layer.options.dashArray.split(/[, ]+/), dashArray = [], dashValue, i;
              for (i = 0; i < parts.length; i++) {
                dashValue = Number(parts[i]);
                if (isNaN(dashValue)) {
                  return;
                }
                dashArray.push(dashValue);
              }
              layer.options._dashArray = dashArray;
            } else {
              layer.options._dashArray = layer.options.dashArray;
            }
          },
          _requestRedraw: function(layer) {
            if (!this._map) {
              return;
            }
            this._extendRedrawBounds(layer);
            this._redrawRequest = this._redrawRequest || requestAnimFrame(this._redraw, this);
          },
          _extendRedrawBounds: function(layer) {
            if (layer._pxBounds) {
              var padding = (layer.options.weight || 0) + 1;
              this._redrawBounds = this._redrawBounds || new Bounds();
              this._redrawBounds.extend(layer._pxBounds.min.subtract([padding, padding]));
              this._redrawBounds.extend(layer._pxBounds.max.add([padding, padding]));
            }
          },
          _redraw: function() {
            this._redrawRequest = null;
            if (this._redrawBounds) {
              this._redrawBounds.min._floor();
              this._redrawBounds.max._ceil();
            }
            this._clear();
            this._draw();
            this._redrawBounds = null;
          },
          _clear: function() {
            var bounds = this._redrawBounds;
            if (bounds) {
              var size = bounds.getSize();
              this._ctx.clearRect(bounds.min.x, bounds.min.y, size.x, size.y);
            } else {
              this._ctx.save();
              this._ctx.setTransform(1, 0, 0, 1, 0, 0);
              this._ctx.clearRect(0, 0, this._container.width, this._container.height);
              this._ctx.restore();
            }
          },
          _draw: function() {
            var layer, bounds = this._redrawBounds;
            this._ctx.save();
            if (bounds) {
              var size = bounds.getSize();
              this._ctx.beginPath();
              this._ctx.rect(bounds.min.x, bounds.min.y, size.x, size.y);
              this._ctx.clip();
            }
            this._drawing = true;
            for (var order = this._drawFirst; order; order = order.next) {
              layer = order.layer;
              if (!bounds || layer._pxBounds && layer._pxBounds.intersects(bounds)) {
                layer._updatePath();
              }
            }
            this._drawing = false;
            this._ctx.restore();
          },
          _updatePoly: function(layer, closed) {
            if (!this._drawing) {
              return;
            }
            var i, j, len2, p, parts = layer._parts, len = parts.length, ctx = this._ctx;
            if (!len) {
              return;
            }
            ctx.beginPath();
            for (i = 0; i < len; i++) {
              for (j = 0, len2 = parts[i].length; j < len2; j++) {
                p = parts[i][j];
                ctx[j ? "lineTo" : "moveTo"](p.x, p.y);
              }
              if (closed) {
                ctx.closePath();
              }
            }
            this._fillStroke(ctx, layer);
          },
          _updateCircle: function(layer) {
            if (!this._drawing || layer._empty()) {
              return;
            }
            var p = layer._point, ctx = this._ctx, r = Math.max(Math.round(layer._radius), 1), s = (Math.max(Math.round(layer._radiusY), 1) || r) / r;
            if (s !== 1) {
              ctx.save();
              ctx.scale(1, s);
            }
            ctx.beginPath();
            ctx.arc(p.x, p.y / s, r, 0, Math.PI * 2, false);
            if (s !== 1) {
              ctx.restore();
            }
            this._fillStroke(ctx, layer);
          },
          _fillStroke: function(ctx, layer) {
            var options = layer.options;
            if (options.fill) {
              ctx.globalAlpha = options.fillOpacity;
              ctx.fillStyle = options.fillColor || options.color;
              ctx.fill(options.fillRule || "evenodd");
            }
            if (options.stroke && options.weight !== 0) {
              if (ctx.setLineDash) {
                ctx.setLineDash(layer.options && layer.options._dashArray || []);
              }
              ctx.globalAlpha = options.opacity;
              ctx.lineWidth = options.weight;
              ctx.strokeStyle = options.color;
              ctx.lineCap = options.lineCap;
              ctx.lineJoin = options.lineJoin;
              ctx.stroke();
            }
          },
          // Canvas obviously doesn't have mouse events for individual drawn objects,
          // so we emulate that by calculating what's under the mouse on mousemove/click manually
          _onClick: function(e) {
            var point = this._map.mouseEventToLayerPoint(e), layer, clickedLayer;
            for (var order = this._drawFirst; order; order = order.next) {
              layer = order.layer;
              if (layer.options.interactive && layer._containsPoint(point)) {
                if (!(e.type === "click" || e.type === "preclick") || !this._map._draggableMoved(layer)) {
                  clickedLayer = layer;
                }
              }
            }
            this._fireEvent(clickedLayer ? [clickedLayer] : false, e);
          },
          _onMouseMove: function(e) {
            if (!this._map || this._map.dragging.moving() || this._map._animatingZoom) {
              return;
            }
            var point = this._map.mouseEventToLayerPoint(e);
            this._handleMouseHover(e, point);
          },
          _handleMouseOut: function(e) {
            var layer = this._hoveredLayer;
            if (layer) {
              removeClass(this._container, "leaflet-interactive");
              this._fireEvent([layer], e, "mouseout");
              this._hoveredLayer = null;
              this._mouseHoverThrottled = false;
            }
          },
          _handleMouseHover: function(e, point) {
            if (this._mouseHoverThrottled) {
              return;
            }
            var layer, candidateHoveredLayer;
            for (var order = this._drawFirst; order; order = order.next) {
              layer = order.layer;
              if (layer.options.interactive && layer._containsPoint(point)) {
                candidateHoveredLayer = layer;
              }
            }
            if (candidateHoveredLayer !== this._hoveredLayer) {
              this._handleMouseOut(e);
              if (candidateHoveredLayer) {
                addClass(this._container, "leaflet-interactive");
                this._fireEvent([candidateHoveredLayer], e, "mouseover");
                this._hoveredLayer = candidateHoveredLayer;
              }
            }
            this._fireEvent(this._hoveredLayer ? [this._hoveredLayer] : false, e);
            this._mouseHoverThrottled = true;
            setTimeout(bind(function() {
              this._mouseHoverThrottled = false;
            }, this), 32);
          },
          _fireEvent: function(layers2, e, type2) {
            this._map._fireDOMEvent(e, type2 || e.type, layers2);
          },
          _bringToFront: function(layer) {
            var order = layer._order;
            if (!order) {
              return;
            }
            var next = order.next;
            var prev = order.prev;
            if (next) {
              next.prev = prev;
            } else {
              return;
            }
            if (prev) {
              prev.next = next;
            } else if (next) {
              this._drawFirst = next;
            }
            order.prev = this._drawLast;
            this._drawLast.next = order;
            order.next = null;
            this._drawLast = order;
            this._requestRedraw(layer);
          },
          _bringToBack: function(layer) {
            var order = layer._order;
            if (!order) {
              return;
            }
            var next = order.next;
            var prev = order.prev;
            if (prev) {
              prev.next = next;
            } else {
              return;
            }
            if (next) {
              next.prev = prev;
            } else if (prev) {
              this._drawLast = prev;
            }
            order.prev = null;
            order.next = this._drawFirst;
            this._drawFirst.prev = order;
            this._drawFirst = order;
            this._requestRedraw(layer);
          }
        });
        function canvas(options) {
          return Browser.canvas ? new Canvas(options) : null;
        }
        var vmlCreate = function() {
          try {
            document.namespaces.add("lvml", "urn:schemas-microsoft-com:vml");
            return function(name) {
              return document.createElement("<lvml:" + name + ' class="lvml">');
            };
          } catch (e) {
          }
          return function(name) {
            return document.createElement("<" + name + ' xmlns="urn:schemas-microsoft.com:vml" class="lvml">');
          };
        }();
        var vmlMixin = {
          _initContainer: function() {
            this._container = create$1("div", "leaflet-vml-container");
          },
          _update: function() {
            if (this._map._animatingZoom) {
              return;
            }
            Renderer.prototype._update.call(this);
            this.fire("update");
          },
          _initPath: function(layer) {
            var container = layer._container = vmlCreate("shape");
            addClass(container, "leaflet-vml-shape " + (this.options.className || ""));
            container.coordsize = "1 1";
            layer._path = vmlCreate("path");
            container.appendChild(layer._path);
            this._updateStyle(layer);
            this._layers[stamp(layer)] = layer;
          },
          _addPath: function(layer) {
            var container = layer._container;
            this._container.appendChild(container);
            if (layer.options.interactive) {
              layer.addInteractiveTarget(container);
            }
          },
          _removePath: function(layer) {
            var container = layer._container;
            remove(container);
            layer.removeInteractiveTarget(container);
            delete this._layers[stamp(layer)];
          },
          _updateStyle: function(layer) {
            var stroke = layer._stroke, fill = layer._fill, options = layer.options, container = layer._container;
            container.stroked = !!options.stroke;
            container.filled = !!options.fill;
            if (options.stroke) {
              if (!stroke) {
                stroke = layer._stroke = vmlCreate("stroke");
              }
              container.appendChild(stroke);
              stroke.weight = options.weight + "px";
              stroke.color = options.color;
              stroke.opacity = options.opacity;
              if (options.dashArray) {
                stroke.dashStyle = isArray(options.dashArray) ? options.dashArray.join(" ") : options.dashArray.replace(/( *, *)/g, " ");
              } else {
                stroke.dashStyle = "";
              }
              stroke.endcap = options.lineCap.replace("butt", "flat");
              stroke.joinstyle = options.lineJoin;
            } else if (stroke) {
              container.removeChild(stroke);
              layer._stroke = null;
            }
            if (options.fill) {
              if (!fill) {
                fill = layer._fill = vmlCreate("fill");
              }
              container.appendChild(fill);
              fill.color = options.fillColor || options.color;
              fill.opacity = options.fillOpacity;
            } else if (fill) {
              container.removeChild(fill);
              layer._fill = null;
            }
          },
          _updateCircle: function(layer) {
            var p = layer._point.round(), r = Math.round(layer._radius), r2 = Math.round(layer._radiusY || r);
            this._setPath(layer, layer._empty() ? "M0 0" : "AL " + p.x + "," + p.y + " " + r + "," + r2 + " 0," + 65535 * 360);
          },
          _setPath: function(layer, path) {
            layer._path.v = path;
          },
          _bringToFront: function(layer) {
            toFront(layer._container);
          },
          _bringToBack: function(layer) {
            toBack(layer._container);
          }
        };
        var create = Browser.vml ? vmlCreate : svgCreate;
        var SVG = Renderer.extend({
          _initContainer: function() {
            this._container = create("svg");
            this._container.setAttribute("pointer-events", "none");
            this._rootGroup = create("g");
            this._container.appendChild(this._rootGroup);
          },
          _destroyContainer: function() {
            remove(this._container);
            off(this._container);
            delete this._container;
            delete this._rootGroup;
            delete this._svgSize;
          },
          _update: function() {
            if (this._map._animatingZoom && this._bounds) {
              return;
            }
            Renderer.prototype._update.call(this);
            var b = this._bounds, size = b.getSize(), container = this._container;
            if (!this._svgSize || !this._svgSize.equals(size)) {
              this._svgSize = size;
              container.setAttribute("width", size.x);
              container.setAttribute("height", size.y);
            }
            setPosition(container, b.min);
            container.setAttribute("viewBox", [b.min.x, b.min.y, size.x, size.y].join(" "));
            this.fire("update");
          },
          // methods below are called by vector layers implementations
          _initPath: function(layer) {
            var path = layer._path = create("path");
            if (layer.options.className) {
              addClass(path, layer.options.className);
            }
            if (layer.options.interactive) {
              addClass(path, "leaflet-interactive");
            }
            this._updateStyle(layer);
            this._layers[stamp(layer)] = layer;
          },
          _addPath: function(layer) {
            if (!this._rootGroup) {
              this._initContainer();
            }
            this._rootGroup.appendChild(layer._path);
            layer.addInteractiveTarget(layer._path);
          },
          _removePath: function(layer) {
            remove(layer._path);
            layer.removeInteractiveTarget(layer._path);
            delete this._layers[stamp(layer)];
          },
          _updatePath: function(layer) {
            layer._project();
            layer._update();
          },
          _updateStyle: function(layer) {
            var path = layer._path, options = layer.options;
            if (!path) {
              return;
            }
            if (options.stroke) {
              path.setAttribute("stroke", options.color);
              path.setAttribute("stroke-opacity", options.opacity);
              path.setAttribute("stroke-width", options.weight);
              path.setAttribute("stroke-linecap", options.lineCap);
              path.setAttribute("stroke-linejoin", options.lineJoin);
              if (options.dashArray) {
                path.setAttribute("stroke-dasharray", options.dashArray);
              } else {
                path.removeAttribute("stroke-dasharray");
              }
              if (options.dashOffset) {
                path.setAttribute("stroke-dashoffset", options.dashOffset);
              } else {
                path.removeAttribute("stroke-dashoffset");
              }
            } else {
              path.setAttribute("stroke", "none");
            }
            if (options.fill) {
              path.setAttribute("fill", options.fillColor || options.color);
              path.setAttribute("fill-opacity", options.fillOpacity);
              path.setAttribute("fill-rule", options.fillRule || "evenodd");
            } else {
              path.setAttribute("fill", "none");
            }
          },
          _updatePoly: function(layer, closed) {
            this._setPath(layer, pointsToPath(layer._parts, closed));
          },
          _updateCircle: function(layer) {
            var p = layer._point, r = Math.max(Math.round(layer._radius), 1), r2 = Math.max(Math.round(layer._radiusY), 1) || r, arc = "a" + r + "," + r2 + " 0 1,0 ";
            var d = layer._empty() ? "M0 0" : "M" + (p.x - r) + "," + p.y + arc + r * 2 + ",0 " + arc + -r * 2 + ",0 ";
            this._setPath(layer, d);
          },
          _setPath: function(layer, path) {
            layer._path.setAttribute("d", path);
          },
          // SVG does not have the concept of zIndex so we resort to changing the DOM order of elements
          _bringToFront: function(layer) {
            toFront(layer._path);
          },
          _bringToBack: function(layer) {
            toBack(layer._path);
          }
        });
        if (Browser.vml) {
          SVG.include(vmlMixin);
        }
        function svg(options) {
          return Browser.svg || Browser.vml ? new SVG(options) : null;
        }
        Map3.include({
          // @namespace Map; @method getRenderer(layer: Path): Renderer
          // Returns the instance of `Renderer` that should be used to render the given
          // `Path`. It will ensure that the `renderer` options of the map and paths
          // are respected, and that the renderers do exist on the map.
          getRenderer: function(layer) {
            var renderer = layer.options.renderer || this._getPaneRenderer(layer.options.pane) || this.options.renderer || this._renderer;
            if (!renderer) {
              renderer = this._renderer = this._createRenderer();
            }
            if (!this.hasLayer(renderer)) {
              this.addLayer(renderer);
            }
            return renderer;
          },
          _getPaneRenderer: function(name) {
            if (name === "overlayPane" || name === void 0) {
              return false;
            }
            var renderer = this._paneRenderers[name];
            if (renderer === void 0) {
              renderer = this._createRenderer({ pane: name });
              this._paneRenderers[name] = renderer;
            }
            return renderer;
          },
          _createRenderer: function(options) {
            return this.options.preferCanvas && canvas(options) || svg(options);
          }
        });
        var Rectangle = Polygon.extend({
          initialize: function(latLngBounds, options) {
            Polygon.prototype.initialize.call(this, this._boundsToLatLngs(latLngBounds), options);
          },
          // @method setBounds(latLngBounds: LatLngBounds): this
          // Redraws the rectangle with the passed bounds.
          setBounds: function(latLngBounds) {
            return this.setLatLngs(this._boundsToLatLngs(latLngBounds));
          },
          _boundsToLatLngs: function(latLngBounds) {
            latLngBounds = toLatLngBounds(latLngBounds);
            return [
              latLngBounds.getSouthWest(),
              latLngBounds.getNorthWest(),
              latLngBounds.getNorthEast(),
              latLngBounds.getSouthEast()
            ];
          }
        });
        function rectangle(latLngBounds, options) {
          return new Rectangle(latLngBounds, options);
        }
        SVG.create = create;
        SVG.pointsToPath = pointsToPath;
        GeoJSON.geometryToLayer = geometryToLayer;
        GeoJSON.coordsToLatLng = coordsToLatLng;
        GeoJSON.coordsToLatLngs = coordsToLatLngs;
        GeoJSON.latLngToCoords = latLngToCoords;
        GeoJSON.latLngsToCoords = latLngsToCoords;
        GeoJSON.getFeature = getFeature;
        GeoJSON.asFeature = asFeature;
        Map3.mergeOptions({
          // @option boxZoom: Boolean = true
          // Whether the map can be zoomed to a rectangular area specified by
          // dragging the mouse while pressing the shift key.
          boxZoom: true
        });
        var BoxZoom = Handler.extend({
          initialize: function(map2) {
            this._map = map2;
            this._container = map2._container;
            this._pane = map2._panes.overlayPane;
            this._resetStateTimeout = 0;
            map2.on("unload", this._destroy, this);
          },
          addHooks: function() {
            on(this._container, "mousedown", this._onMouseDown, this);
          },
          removeHooks: function() {
            off(this._container, "mousedown", this._onMouseDown, this);
          },
          moved: function() {
            return this._moved;
          },
          _destroy: function() {
            remove(this._pane);
            delete this._pane;
          },
          _resetState: function() {
            this._resetStateTimeout = 0;
            this._moved = false;
          },
          _clearDeferredResetState: function() {
            if (this._resetStateTimeout !== 0) {
              clearTimeout(this._resetStateTimeout);
              this._resetStateTimeout = 0;
            }
          },
          _onMouseDown: function(e) {
            if (!e.shiftKey || e.which !== 1 && e.button !== 1) {
              return false;
            }
            this._clearDeferredResetState();
            this._resetState();
            disableTextSelection();
            disableImageDrag();
            this._startPoint = this._map.mouseEventToContainerPoint(e);
            on(document, {
              contextmenu: stop,
              mousemove: this._onMouseMove,
              mouseup: this._onMouseUp,
              keydown: this._onKeyDown
            }, this);
          },
          _onMouseMove: function(e) {
            if (!this._moved) {
              this._moved = true;
              this._box = create$1("div", "leaflet-zoom-box", this._container);
              addClass(this._container, "leaflet-crosshair");
              this._map.fire("boxzoomstart");
            }
            this._point = this._map.mouseEventToContainerPoint(e);
            var bounds = new Bounds(this._point, this._startPoint), size = bounds.getSize();
            setPosition(this._box, bounds.min);
            this._box.style.width = size.x + "px";
            this._box.style.height = size.y + "px";
          },
          _finish: function() {
            if (this._moved) {
              remove(this._box);
              removeClass(this._container, "leaflet-crosshair");
            }
            enableTextSelection();
            enableImageDrag();
            off(document, {
              contextmenu: stop,
              mousemove: this._onMouseMove,
              mouseup: this._onMouseUp,
              keydown: this._onKeyDown
            }, this);
          },
          _onMouseUp: function(e) {
            if (e.which !== 1 && e.button !== 1) {
              return;
            }
            this._finish();
            if (!this._moved) {
              return;
            }
            this._clearDeferredResetState();
            this._resetStateTimeout = setTimeout(bind(this._resetState, this), 0);
            var bounds = new LatLngBounds(
              this._map.containerPointToLatLng(this._startPoint),
              this._map.containerPointToLatLng(this._point)
            );
            this._map.fitBounds(bounds).fire("boxzoomend", { boxZoomBounds: bounds });
          },
          _onKeyDown: function(e) {
            if (e.keyCode === 27) {
              this._finish();
              this._clearDeferredResetState();
              this._resetState();
            }
          }
        });
        Map3.addInitHook("addHandler", "boxZoom", BoxZoom);
        Map3.mergeOptions({
          // @option doubleClickZoom: Boolean|String = true
          // Whether the map can be zoomed in by double clicking on it and
          // zoomed out by double clicking while holding shift. If passed
          // `'center'`, double-click zoom will zoom to the center of the
          //  view regardless of where the mouse was.
          doubleClickZoom: true
        });
        var DoubleClickZoom = Handler.extend({
          addHooks: function() {
            this._map.on("dblclick", this._onDoubleClick, this);
          },
          removeHooks: function() {
            this._map.off("dblclick", this._onDoubleClick, this);
          },
          _onDoubleClick: function(e) {
            var map2 = this._map, oldZoom = map2.getZoom(), delta = map2.options.zoomDelta, zoom2 = e.originalEvent.shiftKey ? oldZoom - delta : oldZoom + delta;
            if (map2.options.doubleClickZoom === "center") {
              map2.setZoom(zoom2);
            } else {
              map2.setZoomAround(e.containerPoint, zoom2);
            }
          }
        });
        Map3.addInitHook("addHandler", "doubleClickZoom", DoubleClickZoom);
        Map3.mergeOptions({
          // @option dragging: Boolean = true
          // Whether the map is draggable with mouse/touch or not.
          dragging: true,
          // @section Panning Inertia Options
          // @option inertia: Boolean = *
          // If enabled, panning of the map will have an inertia effect where
          // the map builds momentum while dragging and continues moving in
          // the same direction for some time. Feels especially nice on touch
          // devices. Enabled by default.
          inertia: true,
          // @option inertiaDeceleration: Number = 3000
          // The rate with which the inertial movement slows down, in pixels/second².
          inertiaDeceleration: 3400,
          // px/s^2
          // @option inertiaMaxSpeed: Number = Infinity
          // Max speed of the inertial movement, in pixels/second.
          inertiaMaxSpeed: Infinity,
          // px/s
          // @option easeLinearity: Number = 0.2
          easeLinearity: 0.2,
          // TODO refactor, move to CRS
          // @option worldCopyJump: Boolean = false
          // With this option enabled, the map tracks when you pan to another "copy"
          // of the world and seamlessly jumps to the original one so that all overlays
          // like markers and vector layers are still visible.
          worldCopyJump: false,
          // @option maxBoundsViscosity: Number = 0.0
          // If `maxBounds` is set, this option will control how solid the bounds
          // are when dragging the map around. The default value of `0.0` allows the
          // user to drag outside the bounds at normal speed, higher values will
          // slow down map dragging outside bounds, and `1.0` makes the bounds fully
          // solid, preventing the user from dragging outside the bounds.
          maxBoundsViscosity: 0
        });
        var Drag = Handler.extend({
          addHooks: function() {
            if (!this._draggable) {
              var map2 = this._map;
              this._draggable = new Draggable(map2._mapPane, map2._container);
              this._draggable.on({
                dragstart: this._onDragStart,
                drag: this._onDrag,
                dragend: this._onDragEnd
              }, this);
              this._draggable.on("predrag", this._onPreDragLimit, this);
              if (map2.options.worldCopyJump) {
                this._draggable.on("predrag", this._onPreDragWrap, this);
                map2.on("zoomend", this._onZoomEnd, this);
                map2.whenReady(this._onZoomEnd, this);
              }
            }
            addClass(this._map._container, "leaflet-grab leaflet-touch-drag");
            this._draggable.enable();
            this._positions = [];
            this._times = [];
          },
          removeHooks: function() {
            removeClass(this._map._container, "leaflet-grab");
            removeClass(this._map._container, "leaflet-touch-drag");
            this._draggable.disable();
          },
          moved: function() {
            return this._draggable && this._draggable._moved;
          },
          moving: function() {
            return this._draggable && this._draggable._moving;
          },
          _onDragStart: function() {
            var map2 = this._map;
            map2._stop();
            if (this._map.options.maxBounds && this._map.options.maxBoundsViscosity) {
              var bounds = toLatLngBounds(this._map.options.maxBounds);
              this._offsetLimit = toBounds(
                this._map.latLngToContainerPoint(bounds.getNorthWest()).multiplyBy(-1),
                this._map.latLngToContainerPoint(bounds.getSouthEast()).multiplyBy(-1).add(this._map.getSize())
              );
              this._viscosity = Math.min(1, Math.max(0, this._map.options.maxBoundsViscosity));
            } else {
              this._offsetLimit = null;
            }
            map2.fire("movestart").fire("dragstart");
            if (map2.options.inertia) {
              this._positions = [];
              this._times = [];
            }
          },
          _onDrag: function(e) {
            if (this._map.options.inertia) {
              var time = this._lastTime = +/* @__PURE__ */ new Date(), pos = this._lastPos = this._draggable._absPos || this._draggable._newPos;
              this._positions.push(pos);
              this._times.push(time);
              this._prunePositions(time);
            }
            this._map.fire("move", e).fire("drag", e);
          },
          _prunePositions: function(time) {
            while (this._positions.length > 1 && time - this._times[0] > 50) {
              this._positions.shift();
              this._times.shift();
            }
          },
          _onZoomEnd: function() {
            var pxCenter = this._map.getSize().divideBy(2), pxWorldCenter = this._map.latLngToLayerPoint([0, 0]);
            this._initialWorldOffset = pxWorldCenter.subtract(pxCenter).x;
            this._worldWidth = this._map.getPixelWorldBounds().getSize().x;
          },
          _viscousLimit: function(value, threshold) {
            return value - (value - threshold) * this._viscosity;
          },
          _onPreDragLimit: function() {
            if (!this._viscosity || !this._offsetLimit) {
              return;
            }
            var offset = this._draggable._newPos.subtract(this._draggable._startPos);
            var limit = this._offsetLimit;
            if (offset.x < limit.min.x) {
              offset.x = this._viscousLimit(offset.x, limit.min.x);
            }
            if (offset.y < limit.min.y) {
              offset.y = this._viscousLimit(offset.y, limit.min.y);
            }
            if (offset.x > limit.max.x) {
              offset.x = this._viscousLimit(offset.x, limit.max.x);
            }
            if (offset.y > limit.max.y) {
              offset.y = this._viscousLimit(offset.y, limit.max.y);
            }
            this._draggable._newPos = this._draggable._startPos.add(offset);
          },
          _onPreDragWrap: function() {
            var worldWidth = this._worldWidth, halfWidth = Math.round(worldWidth / 2), dx = this._initialWorldOffset, x = this._draggable._newPos.x, newX1 = (x - halfWidth + dx) % worldWidth + halfWidth - dx, newX2 = (x + halfWidth + dx) % worldWidth - halfWidth - dx, newX = Math.abs(newX1 + dx) < Math.abs(newX2 + dx) ? newX1 : newX2;
            this._draggable._absPos = this._draggable._newPos.clone();
            this._draggable._newPos.x = newX;
          },
          _onDragEnd: function(e) {
            var map2 = this._map, options = map2.options, noInertia = !options.inertia || e.noInertia || this._times.length < 2;
            map2.fire("dragend", e);
            if (noInertia) {
              map2.fire("moveend");
            } else {
              this._prunePositions(+/* @__PURE__ */ new Date());
              var direction = this._lastPos.subtract(this._positions[0]), duration = (this._lastTime - this._times[0]) / 1e3, ease = options.easeLinearity, speedVector = direction.multiplyBy(ease / duration), speed = speedVector.distanceTo([0, 0]), limitedSpeed = Math.min(options.inertiaMaxSpeed, speed), limitedSpeedVector = speedVector.multiplyBy(limitedSpeed / speed), decelerationDuration = limitedSpeed / (options.inertiaDeceleration * ease), offset = limitedSpeedVector.multiplyBy(-decelerationDuration / 2).round();
              if (!offset.x && !offset.y) {
                map2.fire("moveend");
              } else {
                offset = map2._limitOffset(offset, map2.options.maxBounds);
                requestAnimFrame(function() {
                  map2.panBy(offset, {
                    duration: decelerationDuration,
                    easeLinearity: ease,
                    noMoveStart: true,
                    animate: true
                  });
                });
              }
            }
          }
        });
        Map3.addInitHook("addHandler", "dragging", Drag);
        Map3.mergeOptions({
          // @option keyboard: Boolean = true
          // Makes the map focusable and allows users to navigate the map with keyboard
          // arrows and `+`/`-` keys.
          keyboard: true,
          // @option keyboardPanDelta: Number = 80
          // Amount of pixels to pan when pressing an arrow key.
          keyboardPanDelta: 80
        });
        var Keyboard = Handler.extend({
          keyCodes: {
            left: [37],
            right: [39],
            down: [40],
            up: [38],
            zoomIn: [187, 107, 61, 171],
            zoomOut: [189, 109, 54, 173]
          },
          initialize: function(map2) {
            this._map = map2;
            this._setPanDelta(map2.options.keyboardPanDelta);
            this._setZoomDelta(map2.options.zoomDelta);
          },
          addHooks: function() {
            var container = this._map._container;
            if (container.tabIndex <= 0) {
              container.tabIndex = "0";
            }
            on(container, {
              focus: this._onFocus,
              blur: this._onBlur,
              mousedown: this._onMouseDown
            }, this);
            this._map.on({
              focus: this._addHooks,
              blur: this._removeHooks
            }, this);
          },
          removeHooks: function() {
            this._removeHooks();
            off(this._map._container, {
              focus: this._onFocus,
              blur: this._onBlur,
              mousedown: this._onMouseDown
            }, this);
            this._map.off({
              focus: this._addHooks,
              blur: this._removeHooks
            }, this);
          },
          _onMouseDown: function() {
            if (this._focused) {
              return;
            }
            var body = document.body, docEl = document.documentElement, top = body.scrollTop || docEl.scrollTop, left = body.scrollLeft || docEl.scrollLeft;
            this._map._container.focus();
            window.scrollTo(left, top);
          },
          _onFocus: function() {
            this._focused = true;
            this._map.fire("focus");
          },
          _onBlur: function() {
            this._focused = false;
            this._map.fire("blur");
          },
          _setPanDelta: function(panDelta) {
            var keys = this._panKeys = {}, codes = this.keyCodes, i, len;
            for (i = 0, len = codes.left.length; i < len; i++) {
              keys[codes.left[i]] = [-1 * panDelta, 0];
            }
            for (i = 0, len = codes.right.length; i < len; i++) {
              keys[codes.right[i]] = [panDelta, 0];
            }
            for (i = 0, len = codes.down.length; i < len; i++) {
              keys[codes.down[i]] = [0, panDelta];
            }
            for (i = 0, len = codes.up.length; i < len; i++) {
              keys[codes.up[i]] = [0, -1 * panDelta];
            }
          },
          _setZoomDelta: function(zoomDelta) {
            var keys = this._zoomKeys = {}, codes = this.keyCodes, i, len;
            for (i = 0, len = codes.zoomIn.length; i < len; i++) {
              keys[codes.zoomIn[i]] = zoomDelta;
            }
            for (i = 0, len = codes.zoomOut.length; i < len; i++) {
              keys[codes.zoomOut[i]] = -zoomDelta;
            }
          },
          _addHooks: function() {
            on(document, "keydown", this._onKeyDown, this);
          },
          _removeHooks: function() {
            off(document, "keydown", this._onKeyDown, this);
          },
          _onKeyDown: function(e) {
            if (e.altKey || e.ctrlKey || e.metaKey) {
              return;
            }
            var key = e.keyCode, map2 = this._map, offset;
            if (key in this._panKeys) {
              if (!map2._panAnim || !map2._panAnim._inProgress) {
                offset = this._panKeys[key];
                if (e.shiftKey) {
                  offset = toPoint(offset).multiplyBy(3);
                }
                if (map2.options.maxBounds) {
                  offset = map2._limitOffset(toPoint(offset), map2.options.maxBounds);
                }
                if (map2.options.worldCopyJump) {
                  var newLatLng = map2.wrapLatLng(map2.unproject(map2.project(map2.getCenter()).add(offset)));
                  map2.panTo(newLatLng);
                } else {
                  map2.panBy(offset);
                }
              }
            } else if (key in this._zoomKeys) {
              map2.setZoom(map2.getZoom() + (e.shiftKey ? 3 : 1) * this._zoomKeys[key]);
            } else if (key === 27 && map2._popup && map2._popup.options.closeOnEscapeKey) {
              map2.closePopup();
            } else {
              return;
            }
            stop(e);
          }
        });
        Map3.addInitHook("addHandler", "keyboard", Keyboard);
        Map3.mergeOptions({
          // @section Mouse wheel options
          // @option scrollWheelZoom: Boolean|String = true
          // Whether the map can be zoomed by using the mouse wheel. If passed `'center'`,
          // it will zoom to the center of the view regardless of where the mouse was.
          scrollWheelZoom: true,
          // @option wheelDebounceTime: Number = 40
          // Limits the rate at which a wheel can fire (in milliseconds). By default
          // user can't zoom via wheel more often than once per 40 ms.
          wheelDebounceTime: 40,
          // @option wheelPxPerZoomLevel: Number = 60
          // How many scroll pixels (as reported by [L.DomEvent.getWheelDelta](#domevent-getwheeldelta))
          // mean a change of one full zoom level. Smaller values will make wheel-zooming
          // faster (and vice versa).
          wheelPxPerZoomLevel: 60
        });
        var ScrollWheelZoom = Handler.extend({
          addHooks: function() {
            on(this._map._container, "wheel", this._onWheelScroll, this);
            this._delta = 0;
          },
          removeHooks: function() {
            off(this._map._container, "wheel", this._onWheelScroll, this);
          },
          _onWheelScroll: function(e) {
            var delta = getWheelDelta(e);
            var debounce = this._map.options.wheelDebounceTime;
            this._delta += delta;
            this._lastMousePos = this._map.mouseEventToContainerPoint(e);
            if (!this._startTime) {
              this._startTime = +/* @__PURE__ */ new Date();
            }
            var left = Math.max(debounce - (+/* @__PURE__ */ new Date() - this._startTime), 0);
            clearTimeout(this._timer);
            this._timer = setTimeout(bind(this._performZoom, this), left);
            stop(e);
          },
          _performZoom: function() {
            var map2 = this._map, zoom2 = map2.getZoom(), snap = this._map.options.zoomSnap || 0;
            map2._stop();
            var d2 = this._delta / (this._map.options.wheelPxPerZoomLevel * 4), d3 = 4 * Math.log(2 / (1 + Math.exp(-Math.abs(d2)))) / Math.LN2, d4 = snap ? Math.ceil(d3 / snap) * snap : d3, delta = map2._limitZoom(zoom2 + (this._delta > 0 ? d4 : -d4)) - zoom2;
            this._delta = 0;
            this._startTime = null;
            if (!delta) {
              return;
            }
            if (map2.options.scrollWheelZoom === "center") {
              map2.setZoom(zoom2 + delta);
            } else {
              map2.setZoomAround(this._lastMousePos, zoom2 + delta);
            }
          }
        });
        Map3.addInitHook("addHandler", "scrollWheelZoom", ScrollWheelZoom);
        var tapHoldDelay = 600;
        Map3.mergeOptions({
          // @section Touch interaction options
          // @option tapHold: Boolean
          // Enables simulation of `contextmenu` event, default is `true` for mobile Safari.
          tapHold: Browser.touchNative && Browser.safari && Browser.mobile,
          // @option tapTolerance: Number = 15
          // The max number of pixels a user can shift his finger during touch
          // for it to be considered a valid tap.
          tapTolerance: 15
        });
        var TapHold = Handler.extend({
          addHooks: function() {
            on(this._map._container, "touchstart", this._onDown, this);
          },
          removeHooks: function() {
            off(this._map._container, "touchstart", this._onDown, this);
          },
          _onDown: function(e) {
            clearTimeout(this._holdTimeout);
            if (e.touches.length !== 1) {
              return;
            }
            var first = e.touches[0];
            this._startPos = this._newPos = new Point(first.clientX, first.clientY);
            this._holdTimeout = setTimeout(bind(function() {
              this._cancel();
              if (!this._isTapValid()) {
                return;
              }
              on(document, "touchend", preventDefault);
              on(document, "touchend touchcancel", this._cancelClickPrevent);
              this._simulateEvent("contextmenu", first);
            }, this), tapHoldDelay);
            on(document, "touchend touchcancel contextmenu", this._cancel, this);
            on(document, "touchmove", this._onMove, this);
          },
          _cancelClickPrevent: function cancelClickPrevent() {
            off(document, "touchend", preventDefault);
            off(document, "touchend touchcancel", cancelClickPrevent);
          },
          _cancel: function() {
            clearTimeout(this._holdTimeout);
            off(document, "touchend touchcancel contextmenu", this._cancel, this);
            off(document, "touchmove", this._onMove, this);
          },
          _onMove: function(e) {
            var first = e.touches[0];
            this._newPos = new Point(first.clientX, first.clientY);
          },
          _isTapValid: function() {
            return this._newPos.distanceTo(this._startPos) <= this._map.options.tapTolerance;
          },
          _simulateEvent: function(type2, e) {
            var simulatedEvent = new MouseEvent(type2, {
              bubbles: true,
              cancelable: true,
              view: window,
              // detail: 1,
              screenX: e.screenX,
              screenY: e.screenY,
              clientX: e.clientX,
              clientY: e.clientY
              // button: 2,
              // buttons: 2
            });
            simulatedEvent._simulated = true;
            e.target.dispatchEvent(simulatedEvent);
          }
        });
        Map3.addInitHook("addHandler", "tapHold", TapHold);
        Map3.mergeOptions({
          // @section Touch interaction options
          // @option touchZoom: Boolean|String = *
          // Whether the map can be zoomed by touch-dragging with two fingers. If
          // passed `'center'`, it will zoom to the center of the view regardless of
          // where the touch events (fingers) were. Enabled for touch-capable web
          // browsers.
          touchZoom: Browser.touch,
          // @option bounceAtZoomLimits: Boolean = true
          // Set it to false if you don't want the map to zoom beyond min/max zoom
          // and then bounce back when pinch-zooming.
          bounceAtZoomLimits: true
        });
        var TouchZoom = Handler.extend({
          addHooks: function() {
            addClass(this._map._container, "leaflet-touch-zoom");
            on(this._map._container, "touchstart", this._onTouchStart, this);
          },
          removeHooks: function() {
            removeClass(this._map._container, "leaflet-touch-zoom");
            off(this._map._container, "touchstart", this._onTouchStart, this);
          },
          _onTouchStart: function(e) {
            var map2 = this._map;
            if (!e.touches || e.touches.length !== 2 || map2._animatingZoom || this._zooming) {
              return;
            }
            var p1 = map2.mouseEventToContainerPoint(e.touches[0]), p2 = map2.mouseEventToContainerPoint(e.touches[1]);
            this._centerPoint = map2.getSize()._divideBy(2);
            this._startLatLng = map2.containerPointToLatLng(this._centerPoint);
            if (map2.options.touchZoom !== "center") {
              this._pinchStartLatLng = map2.containerPointToLatLng(p1.add(p2)._divideBy(2));
            }
            this._startDist = p1.distanceTo(p2);
            this._startZoom = map2.getZoom();
            this._moved = false;
            this._zooming = true;
            map2._stop();
            on(document, "touchmove", this._onTouchMove, this);
            on(document, "touchend touchcancel", this._onTouchEnd, this);
            preventDefault(e);
          },
          _onTouchMove: function(e) {
            if (!e.touches || e.touches.length !== 2 || !this._zooming) {
              return;
            }
            var map2 = this._map, p1 = map2.mouseEventToContainerPoint(e.touches[0]), p2 = map2.mouseEventToContainerPoint(e.touches[1]), scale2 = p1.distanceTo(p2) / this._startDist;
            this._zoom = map2.getScaleZoom(scale2, this._startZoom);
            if (!map2.options.bounceAtZoomLimits && (this._zoom < map2.getMinZoom() && scale2 < 1 || this._zoom > map2.getMaxZoom() && scale2 > 1)) {
              this._zoom = map2._limitZoom(this._zoom);
            }
            if (map2.options.touchZoom === "center") {
              this._center = this._startLatLng;
              if (scale2 === 1) {
                return;
              }
            } else {
              var delta = p1._add(p2)._divideBy(2)._subtract(this._centerPoint);
              if (scale2 === 1 && delta.x === 0 && delta.y === 0) {
                return;
              }
              this._center = map2.unproject(map2.project(this._pinchStartLatLng, this._zoom).subtract(delta), this._zoom);
            }
            if (!this._moved) {
              map2._moveStart(true, false);
              this._moved = true;
            }
            cancelAnimFrame(this._animRequest);
            var moveFn = bind(map2._move, map2, this._center, this._zoom, { pinch: true, round: false }, void 0);
            this._animRequest = requestAnimFrame(moveFn, this, true);
            preventDefault(e);
          },
          _onTouchEnd: function() {
            if (!this._moved || !this._zooming) {
              this._zooming = false;
              return;
            }
            this._zooming = false;
            cancelAnimFrame(this._animRequest);
            off(document, "touchmove", this._onTouchMove, this);
            off(document, "touchend touchcancel", this._onTouchEnd, this);
            if (this._map.options.zoomAnimation) {
              this._map._animateZoom(this._center, this._map._limitZoom(this._zoom), true, this._map.options.zoomSnap);
            } else {
              this._map._resetView(this._center, this._map._limitZoom(this._zoom));
            }
          }
        });
        Map3.addInitHook("addHandler", "touchZoom", TouchZoom);
        Map3.BoxZoom = BoxZoom;
        Map3.DoubleClickZoom = DoubleClickZoom;
        Map3.Drag = Drag;
        Map3.Keyboard = Keyboard;
        Map3.ScrollWheelZoom = ScrollWheelZoom;
        Map3.TapHold = TapHold;
        Map3.TouchZoom = TouchZoom;
        exports2.Bounds = Bounds;
        exports2.Browser = Browser;
        exports2.CRS = CRS;
        exports2.Canvas = Canvas;
        exports2.Circle = Circle;
        exports2.CircleMarker = CircleMarker;
        exports2.Class = Class;
        exports2.Control = Control;
        exports2.DivIcon = DivIcon;
        exports2.DivOverlay = DivOverlay;
        exports2.DomEvent = DomEvent;
        exports2.DomUtil = DomUtil;
        exports2.Draggable = Draggable;
        exports2.Evented = Evented;
        exports2.FeatureGroup = FeatureGroup;
        exports2.GeoJSON = GeoJSON;
        exports2.GridLayer = GridLayer;
        exports2.Handler = Handler;
        exports2.Icon = Icon;
        exports2.ImageOverlay = ImageOverlay;
        exports2.LatLng = LatLng;
        exports2.LatLngBounds = LatLngBounds;
        exports2.Layer = Layer;
        exports2.LayerGroup = LayerGroup;
        exports2.LineUtil = LineUtil;
        exports2.Map = Map3;
        exports2.Marker = Marker;
        exports2.Mixin = Mixin;
        exports2.Path = Path;
        exports2.Point = Point;
        exports2.PolyUtil = PolyUtil;
        exports2.Polygon = Polygon;
        exports2.Polyline = Polyline;
        exports2.Popup = Popup;
        exports2.PosAnimation = PosAnimation;
        exports2.Projection = index;
        exports2.Rectangle = Rectangle;
        exports2.Renderer = Renderer;
        exports2.SVG = SVG;
        exports2.SVGOverlay = SVGOverlay;
        exports2.TileLayer = TileLayer;
        exports2.Tooltip = Tooltip;
        exports2.Transformation = Transformation;
        exports2.Util = Util;
        exports2.VideoOverlay = VideoOverlay;
        exports2.bind = bind;
        exports2.bounds = toBounds;
        exports2.canvas = canvas;
        exports2.circle = circle;
        exports2.circleMarker = circleMarker;
        exports2.control = control;
        exports2.divIcon = divIcon;
        exports2.extend = extend;
        exports2.featureGroup = featureGroup;
        exports2.geoJSON = geoJSON;
        exports2.geoJson = geoJson;
        exports2.gridLayer = gridLayer;
        exports2.icon = icon;
        exports2.imageOverlay = imageOverlay;
        exports2.latLng = toLatLng;
        exports2.latLngBounds = toLatLngBounds;
        exports2.layerGroup = layerGroup;
        exports2.map = createMap;
        exports2.marker = marker;
        exports2.point = toPoint;
        exports2.polygon = polygon;
        exports2.polyline = polyline;
        exports2.popup = popup;
        exports2.rectangle = rectangle;
        exports2.setOptions = setOptions;
        exports2.stamp = stamp;
        exports2.svg = svg;
        exports2.svgOverlay = svgOverlay;
        exports2.tileLayer = tileLayer;
        exports2.tooltip = tooltip;
        exports2.transformation = toTransformation;
        exports2.version = version;
        exports2.videoOverlay = videoOverlay;
        var oldL = window.L;
        exports2.noConflict = function() {
          window.L = oldL;
          return this;
        };
        window.L = exports2;
      });
    }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/streamlit-component-lib/dist/StreamlitReact.js
  var import_hoist_non_react_statics = __toESM(require_hoist_non_react_statics_cjs());
  var import_react = __toESM(require_react());

  // ../../../../../tmp/agrolattice_component_build/node_modules/tslib/tslib.es6.mjs
  function __rest(s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
      t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
      for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
        if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
          t[p[i]] = s[p[i]];
      }
    return t;
  }
  function __awaiter(thisArg, _arguments, P, generator) {
    function adopt(value) {
      return value instanceof P ? value : new P(function(resolve) {
        resolve(value);
      });
    }
    return new (P || (P = Promise))(function(resolve, reject) {
      function fulfilled(value) {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      }
      function rejected(value) {
        try {
          step(generator["throw"](value));
        } catch (e) {
          reject(e);
        }
      }
      function step(result) {
        result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected);
      }
      step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
  }
  function __values(o) {
    var s = typeof Symbol === "function" && Symbol.iterator, m = s && o[s], i = 0;
    if (m) return m.call(o);
    if (o && typeof o.length === "number") return {
      next: function() {
        if (o && i >= o.length) o = void 0;
        return { value: o && o[i++], done: !o };
      }
    };
    throw new TypeError(s ? "Object is not iterable." : "Symbol.iterator is not defined.");
  }
  function __await(v) {
    return this instanceof __await ? (this.v = v, this) : new __await(v);
  }
  function __asyncGenerator(thisArg, _arguments, generator) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var g = generator.apply(thisArg, _arguments || []), i, q = [];
    return i = Object.create((typeof AsyncIterator === "function" ? AsyncIterator : Object).prototype), verb("next"), verb("throw"), verb("return", awaitReturn), i[Symbol.asyncIterator] = function() {
      return this;
    }, i;
    function awaitReturn(f) {
      return function(v) {
        return Promise.resolve(v).then(f, reject);
      };
    }
    function verb(n, f) {
      if (g[n]) {
        i[n] = function(v) {
          return new Promise(function(a, b) {
            q.push([n, v, a, b]) > 1 || resume(n, v);
          });
        };
        if (f) i[n] = f(i[n]);
      }
    }
    function resume(n, v) {
      try {
        step(g[n](v));
      } catch (e) {
        settle(q[0][3], e);
      }
    }
    function step(r) {
      r.value instanceof __await ? Promise.resolve(r.value.v).then(fulfill, reject) : settle(q[0][2], r);
    }
    function fulfill(value) {
      resume("next", value);
    }
    function reject(value) {
      resume("throw", value);
    }
    function settle(f, v) {
      if (f(v), q.shift(), q.length) resume(q[0][0], q[0][1]);
    }
  }
  function __asyncDelegator(o) {
    var i, p;
    return i = {}, verb("next"), verb("throw", function(e) {
      throw e;
    }), verb("return"), i[Symbol.iterator] = function() {
      return this;
    }, i;
    function verb(n, f) {
      i[n] = o[n] ? function(v) {
        return (p = !p) ? { value: __await(o[n](v)), done: false } : f ? f(v) : v;
      } : f;
    }
  }
  function __asyncValues(o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function() {
      return this;
    }, i);
    function verb(n) {
      i[n] = o[n] && function(v) {
        return new Promise(function(resolve, reject) {
          v = o[n](v), settle(resolve, reject, v.done, v.value);
        });
      };
    }
    function settle(resolve, reject, d, v) {
      Promise.resolve(v).then(function(v2) {
        resolve({ value: v2, done: d });
      }, reject);
    }
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/buffer.mjs
  var buffer_exports = {};
  __export(buffer_exports, {
    compareArrayLike: () => compareArrayLike,
    joinUint8Arrays: () => joinUint8Arrays,
    memcpy: () => memcpy,
    rebaseValueOffsets: () => rebaseValueOffsets,
    toArrayBufferView: () => toArrayBufferView,
    toArrayBufferViewAsyncIterator: () => toArrayBufferViewAsyncIterator,
    toArrayBufferViewIterator: () => toArrayBufferViewIterator,
    toBigInt64Array: () => toBigInt64Array,
    toBigUint64Array: () => toBigUint64Array,
    toFloat32Array: () => toFloat32Array,
    toFloat32ArrayAsyncIterator: () => toFloat32ArrayAsyncIterator,
    toFloat32ArrayIterator: () => toFloat32ArrayIterator,
    toFloat64Array: () => toFloat64Array,
    toFloat64ArrayAsyncIterator: () => toFloat64ArrayAsyncIterator,
    toFloat64ArrayIterator: () => toFloat64ArrayIterator,
    toInt16Array: () => toInt16Array,
    toInt16ArrayAsyncIterator: () => toInt16ArrayAsyncIterator,
    toInt16ArrayIterator: () => toInt16ArrayIterator,
    toInt32Array: () => toInt32Array,
    toInt32ArrayAsyncIterator: () => toInt32ArrayAsyncIterator,
    toInt32ArrayIterator: () => toInt32ArrayIterator,
    toInt8Array: () => toInt8Array,
    toInt8ArrayAsyncIterator: () => toInt8ArrayAsyncIterator,
    toInt8ArrayIterator: () => toInt8ArrayIterator,
    toUint16Array: () => toUint16Array,
    toUint16ArrayAsyncIterator: () => toUint16ArrayAsyncIterator,
    toUint16ArrayIterator: () => toUint16ArrayIterator,
    toUint32Array: () => toUint32Array,
    toUint32ArrayAsyncIterator: () => toUint32ArrayAsyncIterator,
    toUint32ArrayIterator: () => toUint32ArrayIterator,
    toUint8Array: () => toUint8Array,
    toUint8ArrayAsyncIterator: () => toUint8ArrayAsyncIterator,
    toUint8ArrayIterator: () => toUint8ArrayIterator,
    toUint8ClampedArray: () => toUint8ClampedArray,
    toUint8ClampedArrayAsyncIterator: () => toUint8ClampedArrayAsyncIterator,
    toUint8ClampedArrayIterator: () => toUint8ClampedArrayIterator
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/utf8.mjs
  var decoder = new TextDecoder("utf-8");
  var decodeUtf8 = (buffer) => decoder.decode(buffer);
  var encoder = new TextEncoder();
  var encodeUtf8 = (value) => encoder.encode(value);

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/compat.mjs
  var [BigIntCtor, BigIntAvailable] = (() => {
    const BigIntUnavailableError = () => {
      throw new Error("BigInt is not available in this environment");
    };
    function BigIntUnavailable() {
      throw BigIntUnavailableError();
    }
    BigIntUnavailable.asIntN = () => {
      throw BigIntUnavailableError();
    };
    BigIntUnavailable.asUintN = () => {
      throw BigIntUnavailableError();
    };
    return typeof BigInt !== "undefined" ? [BigInt, true] : [BigIntUnavailable, false];
  })();
  var [BigInt64ArrayCtor, BigInt64ArrayAvailable] = (() => {
    const BigInt64ArrayUnavailableError = () => {
      throw new Error("BigInt64Array is not available in this environment");
    };
    class BigInt64ArrayUnavailable {
      static get BYTES_PER_ELEMENT() {
        return 8;
      }
      static of() {
        throw BigInt64ArrayUnavailableError();
      }
      static from() {
        throw BigInt64ArrayUnavailableError();
      }
      constructor() {
        throw BigInt64ArrayUnavailableError();
      }
    }
    return typeof BigInt64Array !== "undefined" ? [BigInt64Array, true] : [BigInt64ArrayUnavailable, false];
  })();
  var [BigUint64ArrayCtor, BigUint64ArrayAvailable] = (() => {
    const BigUint64ArrayUnavailableError = () => {
      throw new Error("BigUint64Array is not available in this environment");
    };
    class BigUint64ArrayUnavailable {
      static get BYTES_PER_ELEMENT() {
        return 8;
      }
      static of() {
        throw BigUint64ArrayUnavailableError();
      }
      static from() {
        throw BigUint64ArrayUnavailableError();
      }
      constructor() {
        throw BigUint64ArrayUnavailableError();
      }
    }
    return typeof BigUint64Array !== "undefined" ? [BigUint64Array, true] : [BigUint64ArrayUnavailable, false];
  })();
  var isNumber = (x) => typeof x === "number";
  var isBoolean = (x) => typeof x === "boolean";
  var isFunction = (x) => typeof x === "function";
  var isObject = (x) => x != null && Object(x) === x;
  var isPromise = (x) => {
    return isObject(x) && isFunction(x.then);
  };
  var isIterable = (x) => {
    return isObject(x) && isFunction(x[Symbol.iterator]);
  };
  var isAsyncIterable = (x) => {
    return isObject(x) && isFunction(x[Symbol.asyncIterator]);
  };
  var isArrowJSON = (x) => {
    return isObject(x) && isObject(x["schema"]);
  };
  var isIteratorResult = (x) => {
    return isObject(x) && "done" in x && "value" in x;
  };
  var isFileHandle = (x) => {
    return isObject(x) && isFunction(x["stat"]) && isNumber(x["fd"]);
  };
  var isFetchResponse = (x) => {
    return isObject(x) && isReadableDOMStream(x["body"]);
  };
  var isReadableInterop = (x) => "_getDOMStream" in x && "_getNodeStream" in x;
  var isWritableDOMStream = (x) => {
    return isObject(x) && isFunction(x["abort"]) && isFunction(x["getWriter"]) && !isReadableInterop(x);
  };
  var isReadableDOMStream = (x) => {
    return isObject(x) && isFunction(x["cancel"]) && isFunction(x["getReader"]) && !isReadableInterop(x);
  };
  var isWritableNodeStream = (x) => {
    return isObject(x) && isFunction(x["end"]) && isFunction(x["write"]) && isBoolean(x["writable"]) && !isReadableInterop(x);
  };
  var isReadableNodeStream = (x) => {
    return isObject(x) && isFunction(x["read"]) && isFunction(x["pipe"]) && isBoolean(x["readable"]) && !isReadableInterop(x);
  };
  var isFlatbuffersByteBuffer = (x) => {
    return isObject(x) && isFunction(x["clear"]) && isFunction(x["bytes"]) && isFunction(x["position"]) && isFunction(x["setPosition"]) && isFunction(x["capacity"]) && isFunction(x["getBufferIdentifier"]) && isFunction(x["createLong"]);
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/buffer.mjs
  var SharedArrayBuf = typeof SharedArrayBuffer !== "undefined" ? SharedArrayBuffer : ArrayBuffer;
  function collapseContiguousByteRanges(chunks) {
    const result = chunks[0] ? [chunks[0]] : [];
    let xOffset, yOffset, xLen, yLen;
    for (let x, y, i = 0, j = 0, n = chunks.length; ++i < n; ) {
      x = result[j];
      y = chunks[i];
      if (!x || !y || x.buffer !== y.buffer || y.byteOffset < x.byteOffset) {
        y && (result[++j] = y);
        continue;
      }
      ({ byteOffset: xOffset, byteLength: xLen } = x);
      ({ byteOffset: yOffset, byteLength: yLen } = y);
      if (xOffset + xLen < yOffset || yOffset + yLen < xOffset) {
        y && (result[++j] = y);
        continue;
      }
      result[j] = new Uint8Array(x.buffer, xOffset, yOffset - xOffset + yLen);
    }
    return result;
  }
  function memcpy(target, source, targetByteOffset = 0, sourceByteLength = source.byteLength) {
    const targetByteLength = target.byteLength;
    const dst = new Uint8Array(target.buffer, target.byteOffset, targetByteLength);
    const src = new Uint8Array(source.buffer, source.byteOffset, Math.min(sourceByteLength, targetByteLength));
    dst.set(src, targetByteOffset);
    return target;
  }
  function joinUint8Arrays(chunks, size) {
    const result = collapseContiguousByteRanges(chunks);
    const byteLength = result.reduce((x, b) => x + b.byteLength, 0);
    let source, sliced, buffer;
    let offset = 0, index = -1;
    const length = Math.min(size || Number.POSITIVE_INFINITY, byteLength);
    for (const n = result.length; ++index < n; ) {
      source = result[index];
      sliced = source.subarray(0, Math.min(source.length, length - offset));
      if (length <= offset + sliced.length) {
        if (sliced.length < source.length) {
          result[index] = source.subarray(sliced.length);
        } else if (sliced.length === source.length) {
          index++;
        }
        buffer ? memcpy(buffer, sliced, offset) : buffer = sliced;
        break;
      }
      memcpy(buffer || (buffer = new Uint8Array(length)), sliced, offset);
      offset += sliced.length;
    }
    return [buffer || new Uint8Array(0), result.slice(index), byteLength - (buffer ? buffer.byteLength : 0)];
  }
  function toArrayBufferView(ArrayBufferViewCtor, input) {
    let value = isIteratorResult(input) ? input.value : input;
    if (value instanceof ArrayBufferViewCtor) {
      if (ArrayBufferViewCtor === Uint8Array) {
        return new ArrayBufferViewCtor(value.buffer, value.byteOffset, value.byteLength);
      }
      return value;
    }
    if (!value) {
      return new ArrayBufferViewCtor(0);
    }
    if (typeof value === "string") {
      value = encodeUtf8(value);
    }
    if (value instanceof ArrayBuffer) {
      return new ArrayBufferViewCtor(value);
    }
    if (value instanceof SharedArrayBuf) {
      return new ArrayBufferViewCtor(value);
    }
    if (isFlatbuffersByteBuffer(value)) {
      return toArrayBufferView(ArrayBufferViewCtor, value.bytes());
    }
    return !ArrayBuffer.isView(value) ? ArrayBufferViewCtor.from(value) : value.byteLength <= 0 ? new ArrayBufferViewCtor(0) : new ArrayBufferViewCtor(value.buffer, value.byteOffset, value.byteLength / ArrayBufferViewCtor.BYTES_PER_ELEMENT);
  }
  var toInt8Array = (input) => toArrayBufferView(Int8Array, input);
  var toInt16Array = (input) => toArrayBufferView(Int16Array, input);
  var toInt32Array = (input) => toArrayBufferView(Int32Array, input);
  var toBigInt64Array = (input) => toArrayBufferView(BigInt64ArrayCtor, input);
  var toUint8Array = (input) => toArrayBufferView(Uint8Array, input);
  var toUint16Array = (input) => toArrayBufferView(Uint16Array, input);
  var toUint32Array = (input) => toArrayBufferView(Uint32Array, input);
  var toBigUint64Array = (input) => toArrayBufferView(BigUint64ArrayCtor, input);
  var toFloat32Array = (input) => toArrayBufferView(Float32Array, input);
  var toFloat64Array = (input) => toArrayBufferView(Float64Array, input);
  var toUint8ClampedArray = (input) => toArrayBufferView(Uint8ClampedArray, input);
  var pump = (iterator) => {
    iterator.next();
    return iterator;
  };
  function* toArrayBufferViewIterator(ArrayCtor, source) {
    const wrap = function* (x) {
      yield x;
    };
    const buffers = typeof source === "string" ? wrap(source) : ArrayBuffer.isView(source) ? wrap(source) : source instanceof ArrayBuffer ? wrap(source) : source instanceof SharedArrayBuf ? wrap(source) : !isIterable(source) ? wrap(source) : source;
    yield* pump(function* (it) {
      let r = null;
      do {
        r = it.next(yield toArrayBufferView(ArrayCtor, r));
      } while (!r.done);
    }(buffers[Symbol.iterator]()));
    return new ArrayCtor();
  }
  var toInt8ArrayIterator = (input) => toArrayBufferViewIterator(Int8Array, input);
  var toInt16ArrayIterator = (input) => toArrayBufferViewIterator(Int16Array, input);
  var toInt32ArrayIterator = (input) => toArrayBufferViewIterator(Int32Array, input);
  var toUint8ArrayIterator = (input) => toArrayBufferViewIterator(Uint8Array, input);
  var toUint16ArrayIterator = (input) => toArrayBufferViewIterator(Uint16Array, input);
  var toUint32ArrayIterator = (input) => toArrayBufferViewIterator(Uint32Array, input);
  var toFloat32ArrayIterator = (input) => toArrayBufferViewIterator(Float32Array, input);
  var toFloat64ArrayIterator = (input) => toArrayBufferViewIterator(Float64Array, input);
  var toUint8ClampedArrayIterator = (input) => toArrayBufferViewIterator(Uint8ClampedArray, input);
  function toArrayBufferViewAsyncIterator(ArrayCtor, source) {
    return __asyncGenerator(this, arguments, function* toArrayBufferViewAsyncIterator_1() {
      if (isPromise(source)) {
        return yield __await(yield __await(yield* __asyncDelegator(__asyncValues(toArrayBufferViewAsyncIterator(ArrayCtor, yield __await(source))))));
      }
      const wrap = function(x) {
        return __asyncGenerator(this, arguments, function* () {
          yield yield __await(yield __await(x));
        });
      };
      const emit = function(source2) {
        return __asyncGenerator(this, arguments, function* () {
          yield __await(yield* __asyncDelegator(__asyncValues(pump(function* (it) {
            let r = null;
            do {
              r = it.next(yield r === null || r === void 0 ? void 0 : r.value);
            } while (!r.done);
          }(source2[Symbol.iterator]())))));
        });
      };
      const buffers = typeof source === "string" ? wrap(source) : ArrayBuffer.isView(source) ? wrap(source) : source instanceof ArrayBuffer ? wrap(source) : source instanceof SharedArrayBuf ? wrap(source) : isIterable(source) ? emit(source) : !isAsyncIterable(source) ? wrap(source) : source;
      yield __await(
        // otherwise if AsyncIterable, use it
        yield* __asyncDelegator(__asyncValues(pump(function(it) {
          return __asyncGenerator(this, arguments, function* () {
            let r = null;
            do {
              r = yield __await(it.next(yield yield __await(toArrayBufferView(ArrayCtor, r))));
            } while (!r.done);
          });
        }(buffers[Symbol.asyncIterator]()))))
      );
      return yield __await(new ArrayCtor());
    });
  }
  var toInt8ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Int8Array, input);
  var toInt16ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Int16Array, input);
  var toInt32ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Int32Array, input);
  var toUint8ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Uint8Array, input);
  var toUint16ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Uint16Array, input);
  var toUint32ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Uint32Array, input);
  var toFloat32ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Float32Array, input);
  var toFloat64ArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Float64Array, input);
  var toUint8ClampedArrayAsyncIterator = (input) => toArrayBufferViewAsyncIterator(Uint8ClampedArray, input);
  function rebaseValueOffsets(offset, length, valueOffsets) {
    if (offset !== 0) {
      valueOffsets = valueOffsets.slice(0, length + 1);
      for (let i = -1; ++i <= length; ) {
        valueOffsets[i] += offset;
      }
    }
    return valueOffsets;
  }
  function compareArrayLike(a, b) {
    let i = 0;
    const n = a.length;
    if (n !== b.length) {
      return false;
    }
    if (n > 0) {
      do {
        if (a[i] !== b[i]) {
          return false;
        }
      } while (++i < n);
    }
    return true;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/adapters.mjs
  var adapters_default = {
    fromIterable(source) {
      return pump2(fromIterable(source));
    },
    fromAsyncIterable(source) {
      return pump2(fromAsyncIterable(source));
    },
    fromDOMStream(source) {
      return pump2(fromDOMStream(source));
    },
    fromNodeStream(stream) {
      return pump2(fromNodeStream(stream));
    },
    // @ts-ignore
    toDOMStream(source, options) {
      throw new Error(`"toDOMStream" not available in this environment`);
    },
    // @ts-ignore
    toNodeStream(source, options) {
      throw new Error(`"toNodeStream" not available in this environment`);
    }
  };
  var pump2 = (iterator) => {
    iterator.next();
    return iterator;
  };
  function* fromIterable(source) {
    let done, threw = false;
    let buffers = [], buffer;
    let cmd, size, bufferLength = 0;
    function byteRange() {
      if (cmd === "peek") {
        return joinUint8Arrays(buffers, size)[0];
      }
      [buffer, buffers, bufferLength] = joinUint8Arrays(buffers, size);
      return buffer;
    }
    ({ cmd, size } = yield null);
    const it = toUint8ArrayIterator(source)[Symbol.iterator]();
    try {
      do {
        ({ done, value: buffer } = Number.isNaN(size - bufferLength) ? it.next() : it.next(size - bufferLength));
        if (!done && buffer.byteLength > 0) {
          buffers.push(buffer);
          bufferLength += buffer.byteLength;
        }
        if (done || size <= bufferLength) {
          do {
            ({ cmd, size } = yield byteRange());
          } while (size < bufferLength);
        }
      } while (!done);
    } catch (e) {
      (threw = true) && typeof it.throw === "function" && it.throw(e);
    } finally {
      threw === false && typeof it.return === "function" && it.return(null);
    }
    return null;
  }
  function fromAsyncIterable(source) {
    return __asyncGenerator(this, arguments, function* fromAsyncIterable_1() {
      let done, threw = false;
      let buffers = [], buffer;
      let cmd, size, bufferLength = 0;
      function byteRange() {
        if (cmd === "peek") {
          return joinUint8Arrays(buffers, size)[0];
        }
        [buffer, buffers, bufferLength] = joinUint8Arrays(buffers, size);
        return buffer;
      }
      ({ cmd, size } = yield yield __await(null));
      const it = toUint8ArrayAsyncIterator(source)[Symbol.asyncIterator]();
      try {
        do {
          ({ done, value: buffer } = Number.isNaN(size - bufferLength) ? yield __await(it.next()) : yield __await(it.next(size - bufferLength)));
          if (!done && buffer.byteLength > 0) {
            buffers.push(buffer);
            bufferLength += buffer.byteLength;
          }
          if (done || size <= bufferLength) {
            do {
              ({ cmd, size } = yield yield __await(byteRange()));
            } while (size < bufferLength);
          }
        } while (!done);
      } catch (e) {
        (threw = true) && typeof it.throw === "function" && (yield __await(it.throw(e)));
      } finally {
        threw === false && typeof it.return === "function" && (yield __await(it.return(new Uint8Array(0))));
      }
      return yield __await(null);
    });
  }
  function fromDOMStream(source) {
    return __asyncGenerator(this, arguments, function* fromDOMStream_1() {
      let done = false, threw = false;
      let buffers = [], buffer;
      let cmd, size, bufferLength = 0;
      function byteRange() {
        if (cmd === "peek") {
          return joinUint8Arrays(buffers, size)[0];
        }
        [buffer, buffers, bufferLength] = joinUint8Arrays(buffers, size);
        return buffer;
      }
      ({ cmd, size } = yield yield __await(null));
      const it = new AdaptiveByteReader(source);
      try {
        do {
          ({ done, value: buffer } = Number.isNaN(size - bufferLength) ? yield __await(it["read"]()) : yield __await(it["read"](size - bufferLength)));
          if (!done && buffer.byteLength > 0) {
            buffers.push(toUint8Array(buffer));
            bufferLength += buffer.byteLength;
          }
          if (done || size <= bufferLength) {
            do {
              ({ cmd, size } = yield yield __await(byteRange()));
            } while (size < bufferLength);
          }
        } while (!done);
      } catch (e) {
        (threw = true) && (yield __await(it["cancel"](e)));
      } finally {
        threw === false ? yield __await(it["cancel"]()) : source["locked"] && it.releaseLock();
      }
      return yield __await(null);
    });
  }
  var AdaptiveByteReader = class {
    constructor(source) {
      this.source = source;
      this.reader = null;
      this.reader = this.source["getReader"]();
      this.reader["closed"].catch(() => {
      });
    }
    get closed() {
      return this.reader ? this.reader["closed"].catch(() => {
      }) : Promise.resolve();
    }
    releaseLock() {
      if (this.reader) {
        this.reader.releaseLock();
      }
      this.reader = null;
    }
    cancel(reason) {
      return __awaiter(this, void 0, void 0, function* () {
        const { reader, source } = this;
        reader && (yield reader["cancel"](reason).catch(() => {
        }));
        source && (source["locked"] && this.releaseLock());
      });
    }
    read(size) {
      return __awaiter(this, void 0, void 0, function* () {
        if (size === 0) {
          return { done: this.reader == null, value: new Uint8Array(0) };
        }
        const result = yield this.reader.read();
        !result.done && (result.value = toUint8Array(result));
        return result;
      });
    }
  };
  var onEvent = (stream, event) => {
    const handler = (_) => resolve([event, _]);
    let resolve;
    return [event, handler, new Promise((r) => (resolve = r) && stream["once"](event, handler))];
  };
  function fromNodeStream(stream) {
    return __asyncGenerator(this, arguments, function* fromNodeStream_1() {
      const events = [];
      let event = "error";
      let done = false, err = null;
      let cmd, size, bufferLength = 0;
      let buffers = [], buffer;
      function byteRange() {
        if (cmd === "peek") {
          return joinUint8Arrays(buffers, size)[0];
        }
        [buffer, buffers, bufferLength] = joinUint8Arrays(buffers, size);
        return buffer;
      }
      ({ cmd, size } = yield yield __await(null));
      if (stream["isTTY"]) {
        yield yield __await(new Uint8Array(0));
        return yield __await(null);
      }
      try {
        events[0] = onEvent(stream, "end");
        events[1] = onEvent(stream, "error");
        do {
          events[2] = onEvent(stream, "readable");
          [event, err] = yield __await(Promise.race(events.map((x) => x[2])));
          if (event === "error") {
            break;
          }
          if (!(done = event === "end")) {
            if (!Number.isFinite(size - bufferLength)) {
              buffer = toUint8Array(stream["read"]());
            } else {
              buffer = toUint8Array(stream["read"](size - bufferLength));
              if (buffer.byteLength < size - bufferLength) {
                buffer = toUint8Array(stream["read"]());
              }
            }
            if (buffer.byteLength > 0) {
              buffers.push(buffer);
              bufferLength += buffer.byteLength;
            }
          }
          if (done || size <= bufferLength) {
            do {
              ({ cmd, size } = yield yield __await(byteRange()));
            } while (size < bufferLength);
          }
        } while (!done);
      } finally {
        yield __await(cleanup(events, event === "error" ? err : null));
      }
      return yield __await(null);
      function cleanup(events2, err2) {
        buffer = buffers = null;
        return new Promise((resolve, reject) => {
          for (const [evt, fn] of events2) {
            stream["off"](evt, fn);
          }
          try {
            const destroy = stream["destroy"];
            destroy && destroy.call(stream, err2);
            err2 = void 0;
          } catch (e) {
            err2 = e || err2;
          } finally {
            err2 != null ? reject(err2) : resolve();
          }
        });
      }
    });
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/enum.mjs
  var MetadataVersion;
  (function(MetadataVersion3) {
    MetadataVersion3[MetadataVersion3["V1"] = 0] = "V1";
    MetadataVersion3[MetadataVersion3["V2"] = 1] = "V2";
    MetadataVersion3[MetadataVersion3["V3"] = 2] = "V3";
    MetadataVersion3[MetadataVersion3["V4"] = 3] = "V4";
    MetadataVersion3[MetadataVersion3["V5"] = 4] = "V5";
  })(MetadataVersion || (MetadataVersion = {}));
  var UnionMode;
  (function(UnionMode3) {
    UnionMode3[UnionMode3["Sparse"] = 0] = "Sparse";
    UnionMode3[UnionMode3["Dense"] = 1] = "Dense";
  })(UnionMode || (UnionMode = {}));
  var Precision;
  (function(Precision3) {
    Precision3[Precision3["HALF"] = 0] = "HALF";
    Precision3[Precision3["SINGLE"] = 1] = "SINGLE";
    Precision3[Precision3["DOUBLE"] = 2] = "DOUBLE";
  })(Precision || (Precision = {}));
  var DateUnit;
  (function(DateUnit3) {
    DateUnit3[DateUnit3["DAY"] = 0] = "DAY";
    DateUnit3[DateUnit3["MILLISECOND"] = 1] = "MILLISECOND";
  })(DateUnit || (DateUnit = {}));
  var TimeUnit;
  (function(TimeUnit3) {
    TimeUnit3[TimeUnit3["SECOND"] = 0] = "SECOND";
    TimeUnit3[TimeUnit3["MILLISECOND"] = 1] = "MILLISECOND";
    TimeUnit3[TimeUnit3["MICROSECOND"] = 2] = "MICROSECOND";
    TimeUnit3[TimeUnit3["NANOSECOND"] = 3] = "NANOSECOND";
  })(TimeUnit || (TimeUnit = {}));
  var IntervalUnit;
  (function(IntervalUnit3) {
    IntervalUnit3[IntervalUnit3["YEAR_MONTH"] = 0] = "YEAR_MONTH";
    IntervalUnit3[IntervalUnit3["DAY_TIME"] = 1] = "DAY_TIME";
    IntervalUnit3[IntervalUnit3["MONTH_DAY_NANO"] = 2] = "MONTH_DAY_NANO";
  })(IntervalUnit || (IntervalUnit = {}));
  var MessageHeader;
  (function(MessageHeader3) {
    MessageHeader3[MessageHeader3["NONE"] = 0] = "NONE";
    MessageHeader3[MessageHeader3["Schema"] = 1] = "Schema";
    MessageHeader3[MessageHeader3["DictionaryBatch"] = 2] = "DictionaryBatch";
    MessageHeader3[MessageHeader3["RecordBatch"] = 3] = "RecordBatch";
    MessageHeader3[MessageHeader3["Tensor"] = 4] = "Tensor";
    MessageHeader3[MessageHeader3["SparseTensor"] = 5] = "SparseTensor";
  })(MessageHeader || (MessageHeader = {}));
  var Type;
  (function(Type3) {
    Type3[Type3["NONE"] = 0] = "NONE";
    Type3[Type3["Null"] = 1] = "Null";
    Type3[Type3["Int"] = 2] = "Int";
    Type3[Type3["Float"] = 3] = "Float";
    Type3[Type3["Binary"] = 4] = "Binary";
    Type3[Type3["Utf8"] = 5] = "Utf8";
    Type3[Type3["Bool"] = 6] = "Bool";
    Type3[Type3["Decimal"] = 7] = "Decimal";
    Type3[Type3["Date"] = 8] = "Date";
    Type3[Type3["Time"] = 9] = "Time";
    Type3[Type3["Timestamp"] = 10] = "Timestamp";
    Type3[Type3["Interval"] = 11] = "Interval";
    Type3[Type3["List"] = 12] = "List";
    Type3[Type3["Struct"] = 13] = "Struct";
    Type3[Type3["Union"] = 14] = "Union";
    Type3[Type3["FixedSizeBinary"] = 15] = "FixedSizeBinary";
    Type3[Type3["FixedSizeList"] = 16] = "FixedSizeList";
    Type3[Type3["Map"] = 17] = "Map";
    Type3[Type3["Dictionary"] = -1] = "Dictionary";
    Type3[Type3["Int8"] = -2] = "Int8";
    Type3[Type3["Int16"] = -3] = "Int16";
    Type3[Type3["Int32"] = -4] = "Int32";
    Type3[Type3["Int64"] = -5] = "Int64";
    Type3[Type3["Uint8"] = -6] = "Uint8";
    Type3[Type3["Uint16"] = -7] = "Uint16";
    Type3[Type3["Uint32"] = -8] = "Uint32";
    Type3[Type3["Uint64"] = -9] = "Uint64";
    Type3[Type3["Float16"] = -10] = "Float16";
    Type3[Type3["Float32"] = -11] = "Float32";
    Type3[Type3["Float64"] = -12] = "Float64";
    Type3[Type3["DateDay"] = -13] = "DateDay";
    Type3[Type3["DateMillisecond"] = -14] = "DateMillisecond";
    Type3[Type3["TimestampSecond"] = -15] = "TimestampSecond";
    Type3[Type3["TimestampMillisecond"] = -16] = "TimestampMillisecond";
    Type3[Type3["TimestampMicrosecond"] = -17] = "TimestampMicrosecond";
    Type3[Type3["TimestampNanosecond"] = -18] = "TimestampNanosecond";
    Type3[Type3["TimeSecond"] = -19] = "TimeSecond";
    Type3[Type3["TimeMillisecond"] = -20] = "TimeMillisecond";
    Type3[Type3["TimeMicrosecond"] = -21] = "TimeMicrosecond";
    Type3[Type3["TimeNanosecond"] = -22] = "TimeNanosecond";
    Type3[Type3["DenseUnion"] = -23] = "DenseUnion";
    Type3[Type3["SparseUnion"] = -24] = "SparseUnion";
    Type3[Type3["IntervalDayTime"] = -25] = "IntervalDayTime";
    Type3[Type3["IntervalYearMonth"] = -26] = "IntervalYearMonth";
  })(Type || (Type = {}));
  var BufferType;
  (function(BufferType2) {
    BufferType2[BufferType2["OFFSET"] = 0] = "OFFSET";
    BufferType2[BufferType2["DATA"] = 1] = "DATA";
    BufferType2[BufferType2["VALIDITY"] = 2] = "VALIDITY";
    BufferType2[BufferType2["TYPE"] = 3] = "TYPE";
  })(BufferType || (BufferType = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/vector.mjs
  var vector_exports = {};
  __export(vector_exports, {
    clampIndex: () => clampIndex,
    clampRange: () => clampRange,
    createElementComparator: () => createElementComparator
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/pretty.mjs
  var undf = void 0;
  function valueToString(x) {
    if (x === null) {
      return "null";
    }
    if (x === undf) {
      return "undefined";
    }
    switch (typeof x) {
      case "number":
        return `${x}`;
      case "bigint":
        return `${x}`;
      case "string":
        return `"${x}"`;
    }
    if (typeof x[Symbol.toPrimitive] === "function") {
      return x[Symbol.toPrimitive]("string");
    }
    if (ArrayBuffer.isView(x)) {
      if (x instanceof BigInt64ArrayCtor || x instanceof BigUint64ArrayCtor) {
        return `[${[...x].map((x2) => valueToString(x2))}]`;
      }
      return `[${x}]`;
    }
    return ArrayBuffer.isView(x) ? `[${x}]` : JSON.stringify(x, (_, y) => typeof y === "bigint" ? `${y}` : y);
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/bn.mjs
  var bn_exports = {};
  __export(bn_exports, {
    BN: () => BN,
    bignumToBigInt: () => bignumToBigInt,
    bignumToString: () => bignumToString,
    isArrowBigNumSymbol: () => isArrowBigNumSymbol
  });
  var isArrowBigNumSymbol = Symbol.for("isArrowBigNum");
  function BigNum(x, ...xs) {
    if (xs.length === 0) {
      return Object.setPrototypeOf(toArrayBufferView(this["TypedArray"], x), this.constructor.prototype);
    }
    return Object.setPrototypeOf(new this["TypedArray"](x, ...xs), this.constructor.prototype);
  }
  BigNum.prototype[isArrowBigNumSymbol] = true;
  BigNum.prototype.toJSON = function() {
    return `"${bignumToString(this)}"`;
  };
  BigNum.prototype.valueOf = function() {
    return bignumToNumber(this);
  };
  BigNum.prototype.toString = function() {
    return bignumToString(this);
  };
  BigNum.prototype[Symbol.toPrimitive] = function(hint = "default") {
    switch (hint) {
      case "number":
        return bignumToNumber(this);
      case "string":
        return bignumToString(this);
      case "default":
        return bignumToBigInt(this);
    }
    return bignumToString(this);
  };
  function SignedBigNum(...args) {
    return BigNum.apply(this, args);
  }
  function UnsignedBigNum(...args) {
    return BigNum.apply(this, args);
  }
  function DecimalBigNum(...args) {
    return BigNum.apply(this, args);
  }
  Object.setPrototypeOf(SignedBigNum.prototype, Object.create(Int32Array.prototype));
  Object.setPrototypeOf(UnsignedBigNum.prototype, Object.create(Uint32Array.prototype));
  Object.setPrototypeOf(DecimalBigNum.prototype, Object.create(Uint32Array.prototype));
  Object.assign(SignedBigNum.prototype, BigNum.prototype, { "constructor": SignedBigNum, "signed": true, "TypedArray": Int32Array, "BigIntArray": BigInt64ArrayCtor });
  Object.assign(UnsignedBigNum.prototype, BigNum.prototype, { "constructor": UnsignedBigNum, "signed": false, "TypedArray": Uint32Array, "BigIntArray": BigUint64ArrayCtor });
  Object.assign(DecimalBigNum.prototype, BigNum.prototype, { "constructor": DecimalBigNum, "signed": true, "TypedArray": Uint32Array, "BigIntArray": BigUint64ArrayCtor });
  function bignumToNumber(bn) {
    const { buffer, byteOffset, length, "signed": signed } = bn;
    const words = new BigUint64ArrayCtor(buffer, byteOffset, length);
    const negative = signed && words[words.length - 1] & BigInt(1) << BigInt(63);
    let number = negative ? BigInt(1) : BigInt(0);
    let i = BigInt(0);
    if (!negative) {
      for (const word of words) {
        number += word * (BigInt(1) << BigInt(32) * i++);
      }
    } else {
      for (const word of words) {
        number += ~word * (BigInt(1) << BigInt(32) * i++);
      }
      number *= BigInt(-1);
    }
    return number;
  }
  var bignumToString;
  var bignumToBigInt;
  if (!BigIntAvailable) {
    bignumToString = decimalToString;
    bignumToBigInt = bignumToString;
  } else {
    bignumToBigInt = (a) => a.byteLength === 8 ? new a["BigIntArray"](a.buffer, a.byteOffset, 1)[0] : decimalToString(a);
    bignumToString = (a) => a.byteLength === 8 ? `${new a["BigIntArray"](a.buffer, a.byteOffset, 1)[0]}` : decimalToString(a);
  }
  function decimalToString(a) {
    let digits = "";
    const base64 = new Uint32Array(2);
    let base32 = new Uint16Array(a.buffer, a.byteOffset, a.byteLength / 2);
    const checks = new Uint32Array((base32 = new Uint16Array(base32).reverse()).buffer);
    let i = -1;
    const n = base32.length - 1;
    do {
      for (base64[0] = base32[i = 0]; i < n; ) {
        base32[i++] = base64[1] = base64[0] / 10;
        base64[0] = (base64[0] - base64[1] * 10 << 16) + base32[i];
      }
      base32[i] = base64[1] = base64[0] / 10;
      base64[0] = base64[0] - base64[1] * 10;
      digits = `${base64[0]}${digits}`;
    } while (checks[0] || checks[1] || checks[2] || checks[3]);
    return digits !== null && digits !== void 0 ? digits : `0`;
  }
  var BN = class _BN {
    /** @nocollapse */
    static new(num, isSigned) {
      switch (isSigned) {
        case true:
          return new SignedBigNum(num);
        case false:
          return new UnsignedBigNum(num);
      }
      switch (num.constructor) {
        case Int8Array:
        case Int16Array:
        case Int32Array:
        case BigInt64ArrayCtor:
          return new SignedBigNum(num);
      }
      if (num.byteLength === 16) {
        return new DecimalBigNum(num);
      }
      return new UnsignedBigNum(num);
    }
    /** @nocollapse */
    static signed(num) {
      return new SignedBigNum(num);
    }
    /** @nocollapse */
    static unsigned(num) {
      return new UnsignedBigNum(num);
    }
    /** @nocollapse */
    static decimal(num) {
      return new DecimalBigNum(num);
    }
    constructor(num, isSigned) {
      return _BN.new(num, isSigned);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/type.mjs
  var _a;
  var _b;
  var _c;
  var _d;
  var _e;
  var _f;
  var _g;
  var _h;
  var _j;
  var _k;
  var _l;
  var _m;
  var _o;
  var _p;
  var _q;
  var _r;
  var _s;
  var _t;
  var _u;
  var DataType = class _DataType {
    /** @nocollapse */
    static isNull(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Null;
    }
    /** @nocollapse */
    static isInt(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Int;
    }
    /** @nocollapse */
    static isFloat(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Float;
    }
    /** @nocollapse */
    static isBinary(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Binary;
    }
    /** @nocollapse */
    static isUtf8(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Utf8;
    }
    /** @nocollapse */
    static isBool(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Bool;
    }
    /** @nocollapse */
    static isDecimal(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Decimal;
    }
    /** @nocollapse */
    static isDate(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Date;
    }
    /** @nocollapse */
    static isTime(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Time;
    }
    /** @nocollapse */
    static isTimestamp(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Timestamp;
    }
    /** @nocollapse */
    static isInterval(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Interval;
    }
    /** @nocollapse */
    static isList(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.List;
    }
    /** @nocollapse */
    static isStruct(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Struct;
    }
    /** @nocollapse */
    static isUnion(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Union;
    }
    /** @nocollapse */
    static isFixedSizeBinary(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.FixedSizeBinary;
    }
    /** @nocollapse */
    static isFixedSizeList(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.FixedSizeList;
    }
    /** @nocollapse */
    static isMap(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Map;
    }
    /** @nocollapse */
    static isDictionary(x) {
      return (x === null || x === void 0 ? void 0 : x.typeId) === Type.Dictionary;
    }
    /** @nocollapse */
    static isDenseUnion(x) {
      return _DataType.isUnion(x) && x.mode === UnionMode.Dense;
    }
    /** @nocollapse */
    static isSparseUnion(x) {
      return _DataType.isUnion(x) && x.mode === UnionMode.Sparse;
    }
    get typeId() {
      return Type.NONE;
    }
  };
  _a = Symbol.toStringTag;
  DataType[_a] = ((proto) => {
    proto.children = null;
    proto.ArrayType = Array;
    return proto[Symbol.toStringTag] = "DataType";
  })(DataType.prototype);
  var Null = class extends DataType {
    toString() {
      return `Null`;
    }
    get typeId() {
      return Type.Null;
    }
  };
  _b = Symbol.toStringTag;
  Null[_b] = ((proto) => proto[Symbol.toStringTag] = "Null")(Null.prototype);
  var Int_ = class extends DataType {
    constructor(isSigned, bitWidth) {
      super();
      this.isSigned = isSigned;
      this.bitWidth = bitWidth;
    }
    get typeId() {
      return Type.Int;
    }
    get ArrayType() {
      switch (this.bitWidth) {
        case 8:
          return this.isSigned ? Int8Array : Uint8Array;
        case 16:
          return this.isSigned ? Int16Array : Uint16Array;
        case 32:
          return this.isSigned ? Int32Array : Uint32Array;
        case 64:
          return this.isSigned ? BigInt64ArrayCtor : BigUint64ArrayCtor;
      }
      throw new Error(`Unrecognized ${this[Symbol.toStringTag]} type`);
    }
    toString() {
      return `${this.isSigned ? `I` : `Ui`}nt${this.bitWidth}`;
    }
  };
  _c = Symbol.toStringTag;
  Int_[_c] = ((proto) => {
    proto.isSigned = null;
    proto.bitWidth = null;
    return proto[Symbol.toStringTag] = "Int";
  })(Int_.prototype);
  var Int8 = class extends Int_ {
    constructor() {
      super(true, 8);
    }
    get ArrayType() {
      return Int8Array;
    }
  };
  var Int16 = class extends Int_ {
    constructor() {
      super(true, 16);
    }
    get ArrayType() {
      return Int16Array;
    }
  };
  var Int32 = class extends Int_ {
    constructor() {
      super(true, 32);
    }
    get ArrayType() {
      return Int32Array;
    }
  };
  var Int64 = class extends Int_ {
    constructor() {
      super(true, 64);
    }
    get ArrayType() {
      return BigInt64ArrayCtor;
    }
  };
  var Uint8 = class extends Int_ {
    constructor() {
      super(false, 8);
    }
    get ArrayType() {
      return Uint8Array;
    }
  };
  var Uint16 = class extends Int_ {
    constructor() {
      super(false, 16);
    }
    get ArrayType() {
      return Uint16Array;
    }
  };
  var Uint32 = class extends Int_ {
    constructor() {
      super(false, 32);
    }
    get ArrayType() {
      return Uint32Array;
    }
  };
  var Uint64 = class extends Int_ {
    constructor() {
      super(false, 64);
    }
    get ArrayType() {
      return BigUint64ArrayCtor;
    }
  };
  Object.defineProperty(Int8.prototype, "ArrayType", { value: Int8Array });
  Object.defineProperty(Int16.prototype, "ArrayType", { value: Int16Array });
  Object.defineProperty(Int32.prototype, "ArrayType", { value: Int32Array });
  Object.defineProperty(Int64.prototype, "ArrayType", { value: BigInt64ArrayCtor });
  Object.defineProperty(Uint8.prototype, "ArrayType", { value: Uint8Array });
  Object.defineProperty(Uint16.prototype, "ArrayType", { value: Uint16Array });
  Object.defineProperty(Uint32.prototype, "ArrayType", { value: Uint32Array });
  Object.defineProperty(Uint64.prototype, "ArrayType", { value: BigUint64ArrayCtor });
  var Float = class extends DataType {
    constructor(precision) {
      super();
      this.precision = precision;
    }
    get typeId() {
      return Type.Float;
    }
    get ArrayType() {
      switch (this.precision) {
        case Precision.HALF:
          return Uint16Array;
        case Precision.SINGLE:
          return Float32Array;
        case Precision.DOUBLE:
          return Float64Array;
      }
      throw new Error(`Unrecognized ${this[Symbol.toStringTag]} type`);
    }
    toString() {
      return `Float${this.precision << 5 || 16}`;
    }
  };
  _d = Symbol.toStringTag;
  Float[_d] = ((proto) => {
    proto.precision = null;
    return proto[Symbol.toStringTag] = "Float";
  })(Float.prototype);
  var Float16 = class extends Float {
    constructor() {
      super(Precision.HALF);
    }
  };
  var Float32 = class extends Float {
    constructor() {
      super(Precision.SINGLE);
    }
  };
  var Float64 = class extends Float {
    constructor() {
      super(Precision.DOUBLE);
    }
  };
  Object.defineProperty(Float16.prototype, "ArrayType", { value: Uint16Array });
  Object.defineProperty(Float32.prototype, "ArrayType", { value: Float32Array });
  Object.defineProperty(Float64.prototype, "ArrayType", { value: Float64Array });
  var Binary = class extends DataType {
    constructor() {
      super();
    }
    get typeId() {
      return Type.Binary;
    }
    toString() {
      return `Binary`;
    }
  };
  _e = Symbol.toStringTag;
  Binary[_e] = ((proto) => {
    proto.ArrayType = Uint8Array;
    return proto[Symbol.toStringTag] = "Binary";
  })(Binary.prototype);
  var Utf8 = class extends DataType {
    constructor() {
      super();
    }
    get typeId() {
      return Type.Utf8;
    }
    toString() {
      return `Utf8`;
    }
  };
  _f = Symbol.toStringTag;
  Utf8[_f] = ((proto) => {
    proto.ArrayType = Uint8Array;
    return proto[Symbol.toStringTag] = "Utf8";
  })(Utf8.prototype);
  var Bool = class extends DataType {
    constructor() {
      super();
    }
    get typeId() {
      return Type.Bool;
    }
    toString() {
      return `Bool`;
    }
  };
  _g = Symbol.toStringTag;
  Bool[_g] = ((proto) => {
    proto.ArrayType = Uint8Array;
    return proto[Symbol.toStringTag] = "Bool";
  })(Bool.prototype);
  var Decimal = class extends DataType {
    constructor(scale, precision, bitWidth = 128) {
      super();
      this.scale = scale;
      this.precision = precision;
      this.bitWidth = bitWidth;
    }
    get typeId() {
      return Type.Decimal;
    }
    toString() {
      return `Decimal[${this.precision}e${this.scale > 0 ? `+` : ``}${this.scale}]`;
    }
  };
  _h = Symbol.toStringTag;
  Decimal[_h] = ((proto) => {
    proto.scale = null;
    proto.precision = null;
    proto.ArrayType = Uint32Array;
    return proto[Symbol.toStringTag] = "Decimal";
  })(Decimal.prototype);
  var Date_ = class extends DataType {
    constructor(unit) {
      super();
      this.unit = unit;
    }
    get typeId() {
      return Type.Date;
    }
    toString() {
      return `Date${(this.unit + 1) * 32}<${DateUnit[this.unit]}>`;
    }
  };
  _j = Symbol.toStringTag;
  Date_[_j] = ((proto) => {
    proto.unit = null;
    proto.ArrayType = Int32Array;
    return proto[Symbol.toStringTag] = "Date";
  })(Date_.prototype);
  var Time_ = class extends DataType {
    constructor(unit, bitWidth) {
      super();
      this.unit = unit;
      this.bitWidth = bitWidth;
    }
    get typeId() {
      return Type.Time;
    }
    toString() {
      return `Time${this.bitWidth}<${TimeUnit[this.unit]}>`;
    }
    get ArrayType() {
      switch (this.bitWidth) {
        case 32:
          return Int32Array;
        case 64:
          return BigInt64ArrayCtor;
      }
      throw new Error(`Unrecognized ${this[Symbol.toStringTag]} type`);
    }
  };
  _k = Symbol.toStringTag;
  Time_[_k] = ((proto) => {
    proto.unit = null;
    proto.bitWidth = null;
    return proto[Symbol.toStringTag] = "Time";
  })(Time_.prototype);
  var Timestamp_ = class extends DataType {
    constructor(unit, timezone) {
      super();
      this.unit = unit;
      this.timezone = timezone;
    }
    get typeId() {
      return Type.Timestamp;
    }
    toString() {
      return `Timestamp<${TimeUnit[this.unit]}${this.timezone ? `, ${this.timezone}` : ``}>`;
    }
  };
  _l = Symbol.toStringTag;
  Timestamp_[_l] = ((proto) => {
    proto.unit = null;
    proto.timezone = null;
    proto.ArrayType = Int32Array;
    return proto[Symbol.toStringTag] = "Timestamp";
  })(Timestamp_.prototype);
  var Interval_ = class extends DataType {
    constructor(unit) {
      super();
      this.unit = unit;
    }
    get typeId() {
      return Type.Interval;
    }
    toString() {
      return `Interval<${IntervalUnit[this.unit]}>`;
    }
  };
  _m = Symbol.toStringTag;
  Interval_[_m] = ((proto) => {
    proto.unit = null;
    proto.ArrayType = Int32Array;
    return proto[Symbol.toStringTag] = "Interval";
  })(Interval_.prototype);
  var List = class extends DataType {
    constructor(child) {
      super();
      this.children = [child];
    }
    get typeId() {
      return Type.List;
    }
    toString() {
      return `List<${this.valueType}>`;
    }
    get valueType() {
      return this.children[0].type;
    }
    get valueField() {
      return this.children[0];
    }
    get ArrayType() {
      return this.valueType.ArrayType;
    }
  };
  _o = Symbol.toStringTag;
  List[_o] = ((proto) => {
    proto.children = null;
    return proto[Symbol.toStringTag] = "List";
  })(List.prototype);
  var Struct = class extends DataType {
    constructor(children) {
      super();
      this.children = children;
    }
    get typeId() {
      return Type.Struct;
    }
    toString() {
      return `Struct<{${this.children.map((f) => `${f.name}:${f.type}`).join(`, `)}}>`;
    }
  };
  _p = Symbol.toStringTag;
  Struct[_p] = ((proto) => {
    proto.children = null;
    return proto[Symbol.toStringTag] = "Struct";
  })(Struct.prototype);
  var Union_ = class extends DataType {
    constructor(mode, typeIds, children) {
      super();
      this.mode = mode;
      this.children = children;
      this.typeIds = typeIds = Int32Array.from(typeIds);
      this.typeIdToChildIndex = typeIds.reduce((typeIdToChildIndex, typeId, idx) => (typeIdToChildIndex[typeId] = idx) && typeIdToChildIndex || typeIdToChildIndex, /* @__PURE__ */ Object.create(null));
    }
    get typeId() {
      return Type.Union;
    }
    toString() {
      return `${this[Symbol.toStringTag]}<${this.children.map((x) => `${x.type}`).join(` | `)}>`;
    }
  };
  _q = Symbol.toStringTag;
  Union_[_q] = ((proto) => {
    proto.mode = null;
    proto.typeIds = null;
    proto.children = null;
    proto.typeIdToChildIndex = null;
    proto.ArrayType = Int8Array;
    return proto[Symbol.toStringTag] = "Union";
  })(Union_.prototype);
  var FixedSizeBinary = class extends DataType {
    constructor(byteWidth) {
      super();
      this.byteWidth = byteWidth;
    }
    get typeId() {
      return Type.FixedSizeBinary;
    }
    toString() {
      return `FixedSizeBinary[${this.byteWidth}]`;
    }
  };
  _r = Symbol.toStringTag;
  FixedSizeBinary[_r] = ((proto) => {
    proto.byteWidth = null;
    proto.ArrayType = Uint8Array;
    return proto[Symbol.toStringTag] = "FixedSizeBinary";
  })(FixedSizeBinary.prototype);
  var FixedSizeList = class extends DataType {
    constructor(listSize, child) {
      super();
      this.listSize = listSize;
      this.children = [child];
    }
    get typeId() {
      return Type.FixedSizeList;
    }
    get valueType() {
      return this.children[0].type;
    }
    get valueField() {
      return this.children[0];
    }
    get ArrayType() {
      return this.valueType.ArrayType;
    }
    toString() {
      return `FixedSizeList[${this.listSize}]<${this.valueType}>`;
    }
  };
  _s = Symbol.toStringTag;
  FixedSizeList[_s] = ((proto) => {
    proto.children = null;
    proto.listSize = null;
    return proto[Symbol.toStringTag] = "FixedSizeList";
  })(FixedSizeList.prototype);
  var Map_ = class extends DataType {
    constructor(child, keysSorted = false) {
      super();
      this.children = [child];
      this.keysSorted = keysSorted;
    }
    get typeId() {
      return Type.Map;
    }
    get keyType() {
      return this.children[0].type.children[0].type;
    }
    get valueType() {
      return this.children[0].type.children[1].type;
    }
    get childType() {
      return this.children[0].type;
    }
    toString() {
      return `Map<{${this.children[0].type.children.map((f) => `${f.name}:${f.type}`).join(`, `)}}>`;
    }
  };
  _t = Symbol.toStringTag;
  Map_[_t] = ((proto) => {
    proto.children = null;
    proto.keysSorted = null;
    return proto[Symbol.toStringTag] = "Map_";
  })(Map_.prototype);
  var getId = /* @__PURE__ */ ((atomicDictionaryId) => () => ++atomicDictionaryId)(-1);
  var Dictionary = class extends DataType {
    constructor(dictionary, indices, id, isOrdered) {
      super();
      this.indices = indices;
      this.dictionary = dictionary;
      this.isOrdered = isOrdered || false;
      this.id = id == null ? getId() : typeof id === "number" ? id : id.low;
    }
    get typeId() {
      return Type.Dictionary;
    }
    get children() {
      return this.dictionary.children;
    }
    get valueType() {
      return this.dictionary;
    }
    get ArrayType() {
      return this.dictionary.ArrayType;
    }
    toString() {
      return `Dictionary<${this.indices}, ${this.dictionary}>`;
    }
  };
  _u = Symbol.toStringTag;
  Dictionary[_u] = ((proto) => {
    proto.id = null;
    proto.indices = null;
    proto.isOrdered = null;
    proto.dictionary = null;
    return proto[Symbol.toStringTag] = "Dictionary";
  })(Dictionary.prototype);
  function strideForType(type2) {
    const t = type2;
    switch (type2.typeId) {
      case Type.Decimal:
        return type2.bitWidth / 32;
      case Type.Timestamp:
        return 2;
      case Type.Date:
        return 1 + t.unit;
      case Type.Interval:
        return 1 + t.unit;
      // case Type.Int: return 1 + +((t as Int_).bitWidth > 32);
      // case Type.Time: return 1 + +((t as Time_).bitWidth > 32);
      case Type.FixedSizeList:
        return t.listSize;
      case Type.FixedSizeBinary:
        return t.byteWidth;
      default:
        return 1;
    }
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor.mjs
  var Visitor = class {
    visitMany(nodes, ...args) {
      return nodes.map((node, i) => this.visit(node, ...args.map((x) => x[i])));
    }
    visit(...args) {
      return this.getVisitFn(args[0], false).apply(this, args);
    }
    getVisitFn(node, throwIfNotFound = true) {
      return getVisitFn(this, node, throwIfNotFound);
    }
    getVisitFnByTypeId(typeId, throwIfNotFound = true) {
      return getVisitFnByTypeId(this, typeId, throwIfNotFound);
    }
    visitNull(_node, ..._args) {
      return null;
    }
    visitBool(_node, ..._args) {
      return null;
    }
    visitInt(_node, ..._args) {
      return null;
    }
    visitFloat(_node, ..._args) {
      return null;
    }
    visitUtf8(_node, ..._args) {
      return null;
    }
    visitBinary(_node, ..._args) {
      return null;
    }
    visitFixedSizeBinary(_node, ..._args) {
      return null;
    }
    visitDate(_node, ..._args) {
      return null;
    }
    visitTimestamp(_node, ..._args) {
      return null;
    }
    visitTime(_node, ..._args) {
      return null;
    }
    visitDecimal(_node, ..._args) {
      return null;
    }
    visitList(_node, ..._args) {
      return null;
    }
    visitStruct(_node, ..._args) {
      return null;
    }
    visitUnion(_node, ..._args) {
      return null;
    }
    visitDictionary(_node, ..._args) {
      return null;
    }
    visitInterval(_node, ..._args) {
      return null;
    }
    visitFixedSizeList(_node, ..._args) {
      return null;
    }
    visitMap(_node, ..._args) {
      return null;
    }
  };
  function getVisitFn(visitor, node, throwIfNotFound = true) {
    if (typeof node === "number") {
      return getVisitFnByTypeId(visitor, node, throwIfNotFound);
    }
    if (typeof node === "string" && node in Type) {
      return getVisitFnByTypeId(visitor, Type[node], throwIfNotFound);
    }
    if (node && node instanceof DataType) {
      return getVisitFnByTypeId(visitor, inferDType(node), throwIfNotFound);
    }
    if ((node === null || node === void 0 ? void 0 : node.type) && node.type instanceof DataType) {
      return getVisitFnByTypeId(visitor, inferDType(node.type), throwIfNotFound);
    }
    return getVisitFnByTypeId(visitor, Type.NONE, throwIfNotFound);
  }
  function getVisitFnByTypeId(visitor, dtype, throwIfNotFound = true) {
    let fn = null;
    switch (dtype) {
      case Type.Null:
        fn = visitor.visitNull;
        break;
      case Type.Bool:
        fn = visitor.visitBool;
        break;
      case Type.Int:
        fn = visitor.visitInt;
        break;
      case Type.Int8:
        fn = visitor.visitInt8 || visitor.visitInt;
        break;
      case Type.Int16:
        fn = visitor.visitInt16 || visitor.visitInt;
        break;
      case Type.Int32:
        fn = visitor.visitInt32 || visitor.visitInt;
        break;
      case Type.Int64:
        fn = visitor.visitInt64 || visitor.visitInt;
        break;
      case Type.Uint8:
        fn = visitor.visitUint8 || visitor.visitInt;
        break;
      case Type.Uint16:
        fn = visitor.visitUint16 || visitor.visitInt;
        break;
      case Type.Uint32:
        fn = visitor.visitUint32 || visitor.visitInt;
        break;
      case Type.Uint64:
        fn = visitor.visitUint64 || visitor.visitInt;
        break;
      case Type.Float:
        fn = visitor.visitFloat;
        break;
      case Type.Float16:
        fn = visitor.visitFloat16 || visitor.visitFloat;
        break;
      case Type.Float32:
        fn = visitor.visitFloat32 || visitor.visitFloat;
        break;
      case Type.Float64:
        fn = visitor.visitFloat64 || visitor.visitFloat;
        break;
      case Type.Utf8:
        fn = visitor.visitUtf8;
        break;
      case Type.Binary:
        fn = visitor.visitBinary;
        break;
      case Type.FixedSizeBinary:
        fn = visitor.visitFixedSizeBinary;
        break;
      case Type.Date:
        fn = visitor.visitDate;
        break;
      case Type.DateDay:
        fn = visitor.visitDateDay || visitor.visitDate;
        break;
      case Type.DateMillisecond:
        fn = visitor.visitDateMillisecond || visitor.visitDate;
        break;
      case Type.Timestamp:
        fn = visitor.visitTimestamp;
        break;
      case Type.TimestampSecond:
        fn = visitor.visitTimestampSecond || visitor.visitTimestamp;
        break;
      case Type.TimestampMillisecond:
        fn = visitor.visitTimestampMillisecond || visitor.visitTimestamp;
        break;
      case Type.TimestampMicrosecond:
        fn = visitor.visitTimestampMicrosecond || visitor.visitTimestamp;
        break;
      case Type.TimestampNanosecond:
        fn = visitor.visitTimestampNanosecond || visitor.visitTimestamp;
        break;
      case Type.Time:
        fn = visitor.visitTime;
        break;
      case Type.TimeSecond:
        fn = visitor.visitTimeSecond || visitor.visitTime;
        break;
      case Type.TimeMillisecond:
        fn = visitor.visitTimeMillisecond || visitor.visitTime;
        break;
      case Type.TimeMicrosecond:
        fn = visitor.visitTimeMicrosecond || visitor.visitTime;
        break;
      case Type.TimeNanosecond:
        fn = visitor.visitTimeNanosecond || visitor.visitTime;
        break;
      case Type.Decimal:
        fn = visitor.visitDecimal;
        break;
      case Type.List:
        fn = visitor.visitList;
        break;
      case Type.Struct:
        fn = visitor.visitStruct;
        break;
      case Type.Union:
        fn = visitor.visitUnion;
        break;
      case Type.DenseUnion:
        fn = visitor.visitDenseUnion || visitor.visitUnion;
        break;
      case Type.SparseUnion:
        fn = visitor.visitSparseUnion || visitor.visitUnion;
        break;
      case Type.Dictionary:
        fn = visitor.visitDictionary;
        break;
      case Type.Interval:
        fn = visitor.visitInterval;
        break;
      case Type.IntervalDayTime:
        fn = visitor.visitIntervalDayTime || visitor.visitInterval;
        break;
      case Type.IntervalYearMonth:
        fn = visitor.visitIntervalYearMonth || visitor.visitInterval;
        break;
      case Type.FixedSizeList:
        fn = visitor.visitFixedSizeList;
        break;
      case Type.Map:
        fn = visitor.visitMap;
        break;
    }
    if (typeof fn === "function")
      return fn;
    if (!throwIfNotFound)
      return () => null;
    throw new Error(`Unrecognized type '${Type[dtype]}'`);
  }
  function inferDType(type2) {
    switch (type2.typeId) {
      case Type.Null:
        return Type.Null;
      case Type.Int: {
        const { bitWidth, isSigned } = type2;
        switch (bitWidth) {
          case 8:
            return isSigned ? Type.Int8 : Type.Uint8;
          case 16:
            return isSigned ? Type.Int16 : Type.Uint16;
          case 32:
            return isSigned ? Type.Int32 : Type.Uint32;
          case 64:
            return isSigned ? Type.Int64 : Type.Uint64;
        }
        return Type.Int;
      }
      case Type.Float:
        switch (type2.precision) {
          case Precision.HALF:
            return Type.Float16;
          case Precision.SINGLE:
            return Type.Float32;
          case Precision.DOUBLE:
            return Type.Float64;
        }
        return Type.Float;
      case Type.Binary:
        return Type.Binary;
      case Type.Utf8:
        return Type.Utf8;
      case Type.Bool:
        return Type.Bool;
      case Type.Decimal:
        return Type.Decimal;
      case Type.Time:
        switch (type2.unit) {
          case TimeUnit.SECOND:
            return Type.TimeSecond;
          case TimeUnit.MILLISECOND:
            return Type.TimeMillisecond;
          case TimeUnit.MICROSECOND:
            return Type.TimeMicrosecond;
          case TimeUnit.NANOSECOND:
            return Type.TimeNanosecond;
        }
        return Type.Time;
      case Type.Timestamp:
        switch (type2.unit) {
          case TimeUnit.SECOND:
            return Type.TimestampSecond;
          case TimeUnit.MILLISECOND:
            return Type.TimestampMillisecond;
          case TimeUnit.MICROSECOND:
            return Type.TimestampMicrosecond;
          case TimeUnit.NANOSECOND:
            return Type.TimestampNanosecond;
        }
        return Type.Timestamp;
      case Type.Date:
        switch (type2.unit) {
          case DateUnit.DAY:
            return Type.DateDay;
          case DateUnit.MILLISECOND:
            return Type.DateMillisecond;
        }
        return Type.Date;
      case Type.Interval:
        switch (type2.unit) {
          case IntervalUnit.DAY_TIME:
            return Type.IntervalDayTime;
          case IntervalUnit.YEAR_MONTH:
            return Type.IntervalYearMonth;
        }
        return Type.Interval;
      case Type.Map:
        return Type.Map;
      case Type.List:
        return Type.List;
      case Type.Struct:
        return Type.Struct;
      case Type.Union:
        switch (type2.mode) {
          case UnionMode.Dense:
            return Type.DenseUnion;
          case UnionMode.Sparse:
            return Type.SparseUnion;
        }
        return Type.Union;
      case Type.FixedSizeBinary:
        return Type.FixedSizeBinary;
      case Type.FixedSizeList:
        return Type.FixedSizeList;
      case Type.Dictionary:
        return Type.Dictionary;
    }
    throw new Error(`Unrecognized type '${Type[type2.typeId]}'`);
  }
  Visitor.prototype.visitInt8 = null;
  Visitor.prototype.visitInt16 = null;
  Visitor.prototype.visitInt32 = null;
  Visitor.prototype.visitInt64 = null;
  Visitor.prototype.visitUint8 = null;
  Visitor.prototype.visitUint16 = null;
  Visitor.prototype.visitUint32 = null;
  Visitor.prototype.visitUint64 = null;
  Visitor.prototype.visitFloat16 = null;
  Visitor.prototype.visitFloat32 = null;
  Visitor.prototype.visitFloat64 = null;
  Visitor.prototype.visitDateDay = null;
  Visitor.prototype.visitDateMillisecond = null;
  Visitor.prototype.visitTimestampSecond = null;
  Visitor.prototype.visitTimestampMillisecond = null;
  Visitor.prototype.visitTimestampMicrosecond = null;
  Visitor.prototype.visitTimestampNanosecond = null;
  Visitor.prototype.visitTimeSecond = null;
  Visitor.prototype.visitTimeMillisecond = null;
  Visitor.prototype.visitTimeMicrosecond = null;
  Visitor.prototype.visitTimeNanosecond = null;
  Visitor.prototype.visitDenseUnion = null;
  Visitor.prototype.visitSparseUnion = null;
  Visitor.prototype.visitIntervalDayTime = null;
  Visitor.prototype.visitIntervalYearMonth = null;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/math.mjs
  var math_exports = {};
  __export(math_exports, {
    float64ToUint16: () => float64ToUint16,
    uint16ToFloat64: () => uint16ToFloat64
  });
  var f64 = new Float64Array(1);
  var u32 = new Uint32Array(f64.buffer);
  function uint16ToFloat64(h) {
    const expo = (h & 31744) >> 10;
    const sigf = (h & 1023) / 1024;
    const sign = Math.pow(-1, (h & 32768) >> 15);
    switch (expo) {
      case 31:
        return sign * (sigf ? Number.NaN : 1 / 0);
      case 0:
        return sign * (sigf ? 6103515625e-14 * sigf : 0);
    }
    return sign * Math.pow(2, expo - 15) * (1 + sigf);
  }
  function float64ToUint16(d) {
    if (d !== d) {
      return 32256;
    }
    f64[0] = d;
    const sign = (u32[1] & 2147483648) >> 16 & 65535;
    let expo = u32[1] & 2146435072, sigf = 0;
    if (expo >= 1089470464) {
      if (u32[0] > 0) {
        expo = 31744;
      } else {
        expo = (expo & 2080374784) >> 16;
        sigf = (u32[1] & 1048575) >> 10;
      }
    } else if (expo <= 1056964608) {
      sigf = 1048576 + (u32[1] & 1048575);
      sigf = 1048576 + (sigf << (expo >> 20) - 998) >> 21;
      expo = 0;
    } else {
      expo = expo - 1056964608 >> 10;
      sigf = (u32[1] & 1048575) + 512 >> 10;
    }
    return sign | expo | sigf & 65535;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/set.mjs
  var SetVisitor = class extends Visitor {
  };
  function wrapSet(fn) {
    return (data, _1, _2) => {
      if (data.setValid(_1, _2 != null)) {
        return fn(data, _1, _2);
      }
    };
  }
  var setEpochMsToDays = (data, index, epochMs) => {
    data[index] = Math.trunc(epochMs / 864e5);
  };
  var setEpochMsToMillisecondsLong = (data, index, epochMs) => {
    data[index] = Math.trunc(epochMs % 4294967296);
    data[index + 1] = Math.trunc(epochMs / 4294967296);
  };
  var setEpochMsToMicrosecondsLong = (data, index, epochMs) => {
    data[index] = Math.trunc(epochMs * 1e3 % 4294967296);
    data[index + 1] = Math.trunc(epochMs * 1e3 / 4294967296);
  };
  var setEpochMsToNanosecondsLong = (data, index, epochMs) => {
    data[index] = Math.trunc(epochMs * 1e6 % 4294967296);
    data[index + 1] = Math.trunc(epochMs * 1e6 / 4294967296);
  };
  var setVariableWidthBytes = (values, valueOffsets, index, value) => {
    if (index + 1 < valueOffsets.length) {
      const { [index]: x, [index + 1]: y } = valueOffsets;
      values.set(value.subarray(0, y - x), x);
    }
  };
  var setBool = ({ offset, values }, index, val) => {
    const idx = offset + index;
    val ? values[idx >> 3] |= 1 << idx % 8 : values[idx >> 3] &= ~(1 << idx % 8);
  };
  var setInt = ({ values }, index, value) => {
    values[index] = value;
  };
  var setFloat = ({ values }, index, value) => {
    values[index] = value;
  };
  var setFloat16 = ({ values }, index, value) => {
    values[index] = float64ToUint16(value);
  };
  var setAnyFloat = (data, index, value) => {
    switch (data.type.precision) {
      case Precision.HALF:
        return setFloat16(data, index, value);
      case Precision.SINGLE:
      case Precision.DOUBLE:
        return setFloat(data, index, value);
    }
  };
  var setDateDay = ({ values }, index, value) => {
    setEpochMsToDays(values, index, value.valueOf());
  };
  var setDateMillisecond = ({ values }, index, value) => {
    setEpochMsToMillisecondsLong(values, index * 2, value.valueOf());
  };
  var setFixedSizeBinary = ({ stride, values }, index, value) => {
    values.set(value.subarray(0, stride), stride * index);
  };
  var setBinary = ({ values, valueOffsets }, index, value) => setVariableWidthBytes(values, valueOffsets, index, value);
  var setUtf8 = ({ values, valueOffsets }, index, value) => {
    setVariableWidthBytes(values, valueOffsets, index, encodeUtf8(value));
  };
  var setDate = (data, index, value) => {
    data.type.unit === DateUnit.DAY ? setDateDay(data, index, value) : setDateMillisecond(data, index, value);
  };
  var setTimestampSecond = ({ values }, index, value) => setEpochMsToMillisecondsLong(values, index * 2, value / 1e3);
  var setTimestampMillisecond = ({ values }, index, value) => setEpochMsToMillisecondsLong(values, index * 2, value);
  var setTimestampMicrosecond = ({ values }, index, value) => setEpochMsToMicrosecondsLong(values, index * 2, value);
  var setTimestampNanosecond = ({ values }, index, value) => setEpochMsToNanosecondsLong(values, index * 2, value);
  var setTimestamp = (data, index, value) => {
    switch (data.type.unit) {
      case TimeUnit.SECOND:
        return setTimestampSecond(data, index, value);
      case TimeUnit.MILLISECOND:
        return setTimestampMillisecond(data, index, value);
      case TimeUnit.MICROSECOND:
        return setTimestampMicrosecond(data, index, value);
      case TimeUnit.NANOSECOND:
        return setTimestampNanosecond(data, index, value);
    }
  };
  var setTimeSecond = ({ values }, index, value) => {
    values[index] = value;
  };
  var setTimeMillisecond = ({ values }, index, value) => {
    values[index] = value;
  };
  var setTimeMicrosecond = ({ values }, index, value) => {
    values[index] = value;
  };
  var setTimeNanosecond = ({ values }, index, value) => {
    values[index] = value;
  };
  var setTime = (data, index, value) => {
    switch (data.type.unit) {
      case TimeUnit.SECOND:
        return setTimeSecond(data, index, value);
      case TimeUnit.MILLISECOND:
        return setTimeMillisecond(data, index, value);
      case TimeUnit.MICROSECOND:
        return setTimeMicrosecond(data, index, value);
      case TimeUnit.NANOSECOND:
        return setTimeNanosecond(data, index, value);
    }
  };
  var setDecimal = ({ values, stride }, index, value) => {
    values.set(value.subarray(0, stride), stride * index);
  };
  var setList = (data, index, value) => {
    const values = data.children[0];
    const valueOffsets = data.valueOffsets;
    const set = instance.getVisitFn(values);
    if (Array.isArray(value)) {
      for (let idx = -1, itr = valueOffsets[index], end = valueOffsets[index + 1]; itr < end; ) {
        set(values, itr++, value[++idx]);
      }
    } else {
      for (let idx = -1, itr = valueOffsets[index], end = valueOffsets[index + 1]; itr < end; ) {
        set(values, itr++, value.get(++idx));
      }
    }
  };
  var setMap = (data, index, value) => {
    const values = data.children[0];
    const { valueOffsets } = data;
    const set = instance.getVisitFn(values);
    let { [index]: idx, [index + 1]: end } = valueOffsets;
    const entries = value instanceof Map ? value.entries() : Object.entries(value);
    for (const val of entries) {
      set(values, idx, val);
      if (++idx >= end)
        break;
    }
  };
  var _setStructArrayValue = (o, v) => (set, c, _, i) => c && set(c, o, v[i]);
  var _setStructVectorValue = (o, v) => (set, c, _, i) => c && set(c, o, v.get(i));
  var _setStructMapValue = (o, v) => (set, c, f, _) => c && set(c, o, v.get(f.name));
  var _setStructObjectValue = (o, v) => (set, c, f, _) => c && set(c, o, v[f.name]);
  var setStruct = (data, index, value) => {
    const childSetters = data.type.children.map((f) => instance.getVisitFn(f.type));
    const set = value instanceof Map ? _setStructMapValue(index, value) : value instanceof Vector ? _setStructVectorValue(index, value) : Array.isArray(value) ? _setStructArrayValue(index, value) : _setStructObjectValue(index, value);
    data.type.children.forEach((f, i) => set(childSetters[i], data.children[i], f, i));
  };
  var setUnion = (data, index, value) => {
    data.type.mode === UnionMode.Dense ? setDenseUnion(data, index, value) : setSparseUnion(data, index, value);
  };
  var setDenseUnion = (data, index, value) => {
    const childIndex = data.type.typeIdToChildIndex[data.typeIds[index]];
    const child = data.children[childIndex];
    instance.visit(child, data.valueOffsets[index], value);
  };
  var setSparseUnion = (data, index, value) => {
    const childIndex = data.type.typeIdToChildIndex[data.typeIds[index]];
    const child = data.children[childIndex];
    instance.visit(child, index, value);
  };
  var setDictionary = (data, index, value) => {
    var _a5;
    (_a5 = data.dictionary) === null || _a5 === void 0 ? void 0 : _a5.set(data.values[index], value);
  };
  var setIntervalValue = (data, index, value) => {
    data.type.unit === IntervalUnit.DAY_TIME ? setIntervalDayTime(data, index, value) : setIntervalYearMonth(data, index, value);
  };
  var setIntervalDayTime = ({ values }, index, value) => {
    values.set(value.subarray(0, 2), 2 * index);
  };
  var setIntervalYearMonth = ({ values }, index, value) => {
    values[index] = value[0] * 12 + value[1] % 12;
  };
  var setFixedSizeList = (data, index, value) => {
    const { stride } = data;
    const child = data.children[0];
    const set = instance.getVisitFn(child);
    if (Array.isArray(value)) {
      for (let idx = -1, offset = index * stride; ++idx < stride; ) {
        set(child, offset + idx, value[idx]);
      }
    } else {
      for (let idx = -1, offset = index * stride; ++idx < stride; ) {
        set(child, offset + idx, value.get(idx));
      }
    }
  };
  SetVisitor.prototype.visitBool = wrapSet(setBool);
  SetVisitor.prototype.visitInt = wrapSet(setInt);
  SetVisitor.prototype.visitInt8 = wrapSet(setInt);
  SetVisitor.prototype.visitInt16 = wrapSet(setInt);
  SetVisitor.prototype.visitInt32 = wrapSet(setInt);
  SetVisitor.prototype.visitInt64 = wrapSet(setInt);
  SetVisitor.prototype.visitUint8 = wrapSet(setInt);
  SetVisitor.prototype.visitUint16 = wrapSet(setInt);
  SetVisitor.prototype.visitUint32 = wrapSet(setInt);
  SetVisitor.prototype.visitUint64 = wrapSet(setInt);
  SetVisitor.prototype.visitFloat = wrapSet(setAnyFloat);
  SetVisitor.prototype.visitFloat16 = wrapSet(setFloat16);
  SetVisitor.prototype.visitFloat32 = wrapSet(setFloat);
  SetVisitor.prototype.visitFloat64 = wrapSet(setFloat);
  SetVisitor.prototype.visitUtf8 = wrapSet(setUtf8);
  SetVisitor.prototype.visitBinary = wrapSet(setBinary);
  SetVisitor.prototype.visitFixedSizeBinary = wrapSet(setFixedSizeBinary);
  SetVisitor.prototype.visitDate = wrapSet(setDate);
  SetVisitor.prototype.visitDateDay = wrapSet(setDateDay);
  SetVisitor.prototype.visitDateMillisecond = wrapSet(setDateMillisecond);
  SetVisitor.prototype.visitTimestamp = wrapSet(setTimestamp);
  SetVisitor.prototype.visitTimestampSecond = wrapSet(setTimestampSecond);
  SetVisitor.prototype.visitTimestampMillisecond = wrapSet(setTimestampMillisecond);
  SetVisitor.prototype.visitTimestampMicrosecond = wrapSet(setTimestampMicrosecond);
  SetVisitor.prototype.visitTimestampNanosecond = wrapSet(setTimestampNanosecond);
  SetVisitor.prototype.visitTime = wrapSet(setTime);
  SetVisitor.prototype.visitTimeSecond = wrapSet(setTimeSecond);
  SetVisitor.prototype.visitTimeMillisecond = wrapSet(setTimeMillisecond);
  SetVisitor.prototype.visitTimeMicrosecond = wrapSet(setTimeMicrosecond);
  SetVisitor.prototype.visitTimeNanosecond = wrapSet(setTimeNanosecond);
  SetVisitor.prototype.visitDecimal = wrapSet(setDecimal);
  SetVisitor.prototype.visitList = wrapSet(setList);
  SetVisitor.prototype.visitStruct = wrapSet(setStruct);
  SetVisitor.prototype.visitUnion = wrapSet(setUnion);
  SetVisitor.prototype.visitDenseUnion = wrapSet(setDenseUnion);
  SetVisitor.prototype.visitSparseUnion = wrapSet(setSparseUnion);
  SetVisitor.prototype.visitDictionary = wrapSet(setDictionary);
  SetVisitor.prototype.visitInterval = wrapSet(setIntervalValue);
  SetVisitor.prototype.visitIntervalDayTime = wrapSet(setIntervalDayTime);
  SetVisitor.prototype.visitIntervalYearMonth = wrapSet(setIntervalYearMonth);
  SetVisitor.prototype.visitFixedSizeList = wrapSet(setFixedSizeList);
  SetVisitor.prototype.visitMap = wrapSet(setMap);
  var instance = new SetVisitor();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/row/struct.mjs
  var kParent = Symbol.for("parent");
  var kRowIndex = Symbol.for("rowIndex");
  var StructRow = class {
    constructor(parent, rowIndex) {
      this[kParent] = parent;
      this[kRowIndex] = rowIndex;
      return new Proxy(this, new StructRowProxyHandler());
    }
    toArray() {
      return Object.values(this.toJSON());
    }
    toJSON() {
      const i = this[kRowIndex];
      const parent = this[kParent];
      const keys = parent.type.children;
      const json = {};
      for (let j = -1, n = keys.length; ++j < n; ) {
        json[keys[j].name] = instance2.visit(parent.children[j], i);
      }
      return json;
    }
    toString() {
      return `{${[...this].map(([key, val]) => `${valueToString(key)}: ${valueToString(val)}`).join(", ")}}`;
    }
    [Symbol.for("nodejs.util.inspect.custom")]() {
      return this.toString();
    }
    [Symbol.iterator]() {
      return new StructRowIterator(this[kParent], this[kRowIndex]);
    }
  };
  var StructRowIterator = class {
    constructor(data, rowIndex) {
      this.childIndex = 0;
      this.children = data.children;
      this.rowIndex = rowIndex;
      this.childFields = data.type.children;
      this.numChildren = this.childFields.length;
    }
    [Symbol.iterator]() {
      return this;
    }
    next() {
      const i = this.childIndex;
      if (i < this.numChildren) {
        this.childIndex = i + 1;
        return {
          done: false,
          value: [
            this.childFields[i].name,
            instance2.visit(this.children[i], this.rowIndex)
          ]
        };
      }
      return { done: true, value: null };
    }
  };
  Object.defineProperties(StructRow.prototype, {
    [Symbol.toStringTag]: { enumerable: false, configurable: false, value: "Row" },
    [kParent]: { writable: true, enumerable: false, configurable: false, value: null },
    [kRowIndex]: { writable: true, enumerable: false, configurable: false, value: -1 }
  });
  var StructRowProxyHandler = class {
    isExtensible() {
      return false;
    }
    deleteProperty() {
      return false;
    }
    preventExtensions() {
      return true;
    }
    ownKeys(row) {
      return row[kParent].type.children.map((f) => f.name);
    }
    has(row, key) {
      return row[kParent].type.children.findIndex((f) => f.name === key) !== -1;
    }
    getOwnPropertyDescriptor(row, key) {
      if (row[kParent].type.children.findIndex((f) => f.name === key) !== -1) {
        return { writable: true, enumerable: true, configurable: true };
      }
      return;
    }
    get(row, key) {
      if (Reflect.has(row, key)) {
        return row[key];
      }
      const idx = row[kParent].type.children.findIndex((f) => f.name === key);
      if (idx !== -1) {
        const val = instance2.visit(row[kParent].children[idx], row[kRowIndex]);
        Reflect.set(row, key, val);
        return val;
      }
    }
    set(row, key, val) {
      const idx = row[kParent].type.children.findIndex((f) => f.name === key);
      if (idx !== -1) {
        instance.visit(row[kParent].children[idx], row[kRowIndex], val);
        return Reflect.set(row, key, val);
      } else if (Reflect.has(row, key) || typeof key === "symbol") {
        return Reflect.set(row, key, val);
      }
      return false;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/get.mjs
  var GetVisitor = class extends Visitor {
  };
  function wrapGet(fn) {
    return (data, _1) => data.getValid(_1) ? fn(data, _1) : null;
  }
  var epochDaysToMs = (data, index) => 864e5 * data[index];
  var epochMillisecondsLongToMs = (data, index) => 4294967296 * data[index + 1] + (data[index] >>> 0);
  var epochMicrosecondsLongToMs = (data, index) => 4294967296 * (data[index + 1] / 1e3) + (data[index] >>> 0) / 1e3;
  var epochNanosecondsLongToMs = (data, index) => 4294967296 * (data[index + 1] / 1e6) + (data[index] >>> 0) / 1e6;
  var epochMillisecondsToDate = (epochMs) => new Date(epochMs);
  var epochDaysToDate = (data, index) => epochMillisecondsToDate(epochDaysToMs(data, index));
  var epochMillisecondsLongToDate = (data, index) => epochMillisecondsToDate(epochMillisecondsLongToMs(data, index));
  var getNull = (_data, _index) => null;
  var getVariableWidthBytes = (values, valueOffsets, index) => {
    if (index + 1 >= valueOffsets.length) {
      return null;
    }
    const x = valueOffsets[index];
    const y = valueOffsets[index + 1];
    return values.subarray(x, y);
  };
  var getBool = ({ offset, values }, index) => {
    const idx = offset + index;
    const byte = values[idx >> 3];
    return (byte & 1 << idx % 8) !== 0;
  };
  var getDateDay = ({ values }, index) => epochDaysToDate(values, index);
  var getDateMillisecond = ({ values }, index) => epochMillisecondsLongToDate(values, index * 2);
  var getNumeric = ({ stride, values }, index) => values[stride * index];
  var getFloat16 = ({ stride, values }, index) => uint16ToFloat64(values[stride * index]);
  var getBigInts = ({ values }, index) => values[index];
  var getFixedSizeBinary = ({ stride, values }, index) => values.subarray(stride * index, stride * (index + 1));
  var getBinary = ({ values, valueOffsets }, index) => getVariableWidthBytes(values, valueOffsets, index);
  var getUtf8 = ({ values, valueOffsets }, index) => {
    const bytes = getVariableWidthBytes(values, valueOffsets, index);
    return bytes !== null ? decodeUtf8(bytes) : null;
  };
  var getInt = ({ values }, index) => values[index];
  var getFloat = ({ type: type2, values }, index) => type2.precision !== Precision.HALF ? values[index] : uint16ToFloat64(values[index]);
  var getDate = (data, index) => data.type.unit === DateUnit.DAY ? getDateDay(data, index) : getDateMillisecond(data, index);
  var getTimestampSecond = ({ values }, index) => 1e3 * epochMillisecondsLongToMs(values, index * 2);
  var getTimestampMillisecond = ({ values }, index) => epochMillisecondsLongToMs(values, index * 2);
  var getTimestampMicrosecond = ({ values }, index) => epochMicrosecondsLongToMs(values, index * 2);
  var getTimestampNanosecond = ({ values }, index) => epochNanosecondsLongToMs(values, index * 2);
  var getTimestamp = (data, index) => {
    switch (data.type.unit) {
      case TimeUnit.SECOND:
        return getTimestampSecond(data, index);
      case TimeUnit.MILLISECOND:
        return getTimestampMillisecond(data, index);
      case TimeUnit.MICROSECOND:
        return getTimestampMicrosecond(data, index);
      case TimeUnit.NANOSECOND:
        return getTimestampNanosecond(data, index);
    }
  };
  var getTimeSecond = ({ values }, index) => values[index];
  var getTimeMillisecond = ({ values }, index) => values[index];
  var getTimeMicrosecond = ({ values }, index) => values[index];
  var getTimeNanosecond = ({ values }, index) => values[index];
  var getTime = (data, index) => {
    switch (data.type.unit) {
      case TimeUnit.SECOND:
        return getTimeSecond(data, index);
      case TimeUnit.MILLISECOND:
        return getTimeMillisecond(data, index);
      case TimeUnit.MICROSECOND:
        return getTimeMicrosecond(data, index);
      case TimeUnit.NANOSECOND:
        return getTimeNanosecond(data, index);
    }
  };
  var getDecimal = ({ values, stride }, index) => BN.decimal(values.subarray(stride * index, stride * (index + 1)));
  var getList = (data, index) => {
    const { valueOffsets, stride, children } = data;
    const { [index * stride]: begin, [index * stride + 1]: end } = valueOffsets;
    const child = children[0];
    const slice = child.slice(begin, end - begin);
    return new Vector([slice]);
  };
  var getMap = (data, index) => {
    const { valueOffsets, children } = data;
    const { [index]: begin, [index + 1]: end } = valueOffsets;
    const child = children[0];
    return new MapRow(child.slice(begin, end - begin));
  };
  var getStruct = (data, index) => {
    return new StructRow(data, index);
  };
  var getUnion = (data, index) => {
    return data.type.mode === UnionMode.Dense ? getDenseUnion(data, index) : getSparseUnion(data, index);
  };
  var getDenseUnion = (data, index) => {
    const childIndex = data.type.typeIdToChildIndex[data.typeIds[index]];
    const child = data.children[childIndex];
    return instance2.visit(child, data.valueOffsets[index]);
  };
  var getSparseUnion = (data, index) => {
    const childIndex = data.type.typeIdToChildIndex[data.typeIds[index]];
    const child = data.children[childIndex];
    return instance2.visit(child, index);
  };
  var getDictionary = (data, index) => {
    var _a5;
    return (_a5 = data.dictionary) === null || _a5 === void 0 ? void 0 : _a5.get(data.values[index]);
  };
  var getInterval = (data, index) => data.type.unit === IntervalUnit.DAY_TIME ? getIntervalDayTime(data, index) : getIntervalYearMonth(data, index);
  var getIntervalDayTime = ({ values }, index) => values.subarray(2 * index, 2 * (index + 1));
  var getIntervalYearMonth = ({ values }, index) => {
    const interval = values[index];
    const int32s = new Int32Array(2);
    int32s[0] = Math.trunc(interval / 12);
    int32s[1] = Math.trunc(interval % 12);
    return int32s;
  };
  var getFixedSizeList = (data, index) => {
    const { stride, children } = data;
    const child = children[0];
    const slice = child.slice(index * stride, stride);
    return new Vector([slice]);
  };
  GetVisitor.prototype.visitNull = wrapGet(getNull);
  GetVisitor.prototype.visitBool = wrapGet(getBool);
  GetVisitor.prototype.visitInt = wrapGet(getInt);
  GetVisitor.prototype.visitInt8 = wrapGet(getNumeric);
  GetVisitor.prototype.visitInt16 = wrapGet(getNumeric);
  GetVisitor.prototype.visitInt32 = wrapGet(getNumeric);
  GetVisitor.prototype.visitInt64 = wrapGet(getBigInts);
  GetVisitor.prototype.visitUint8 = wrapGet(getNumeric);
  GetVisitor.prototype.visitUint16 = wrapGet(getNumeric);
  GetVisitor.prototype.visitUint32 = wrapGet(getNumeric);
  GetVisitor.prototype.visitUint64 = wrapGet(getBigInts);
  GetVisitor.prototype.visitFloat = wrapGet(getFloat);
  GetVisitor.prototype.visitFloat16 = wrapGet(getFloat16);
  GetVisitor.prototype.visitFloat32 = wrapGet(getNumeric);
  GetVisitor.prototype.visitFloat64 = wrapGet(getNumeric);
  GetVisitor.prototype.visitUtf8 = wrapGet(getUtf8);
  GetVisitor.prototype.visitBinary = wrapGet(getBinary);
  GetVisitor.prototype.visitFixedSizeBinary = wrapGet(getFixedSizeBinary);
  GetVisitor.prototype.visitDate = wrapGet(getDate);
  GetVisitor.prototype.visitDateDay = wrapGet(getDateDay);
  GetVisitor.prototype.visitDateMillisecond = wrapGet(getDateMillisecond);
  GetVisitor.prototype.visitTimestamp = wrapGet(getTimestamp);
  GetVisitor.prototype.visitTimestampSecond = wrapGet(getTimestampSecond);
  GetVisitor.prototype.visitTimestampMillisecond = wrapGet(getTimestampMillisecond);
  GetVisitor.prototype.visitTimestampMicrosecond = wrapGet(getTimestampMicrosecond);
  GetVisitor.prototype.visitTimestampNanosecond = wrapGet(getTimestampNanosecond);
  GetVisitor.prototype.visitTime = wrapGet(getTime);
  GetVisitor.prototype.visitTimeSecond = wrapGet(getTimeSecond);
  GetVisitor.prototype.visitTimeMillisecond = wrapGet(getTimeMillisecond);
  GetVisitor.prototype.visitTimeMicrosecond = wrapGet(getTimeMicrosecond);
  GetVisitor.prototype.visitTimeNanosecond = wrapGet(getTimeNanosecond);
  GetVisitor.prototype.visitDecimal = wrapGet(getDecimal);
  GetVisitor.prototype.visitList = wrapGet(getList);
  GetVisitor.prototype.visitStruct = wrapGet(getStruct);
  GetVisitor.prototype.visitUnion = wrapGet(getUnion);
  GetVisitor.prototype.visitDenseUnion = wrapGet(getDenseUnion);
  GetVisitor.prototype.visitSparseUnion = wrapGet(getSparseUnion);
  GetVisitor.prototype.visitDictionary = wrapGet(getDictionary);
  GetVisitor.prototype.visitInterval = wrapGet(getInterval);
  GetVisitor.prototype.visitIntervalDayTime = wrapGet(getIntervalDayTime);
  GetVisitor.prototype.visitIntervalYearMonth = wrapGet(getIntervalYearMonth);
  GetVisitor.prototype.visitFixedSizeList = wrapGet(getFixedSizeList);
  GetVisitor.prototype.visitMap = wrapGet(getMap);
  var instance2 = new GetVisitor();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/row/map.mjs
  var kKeys = Symbol.for("keys");
  var kVals = Symbol.for("vals");
  var MapRow = class {
    constructor(slice) {
      this[kKeys] = new Vector([slice.children[0]]).memoize();
      this[kVals] = slice.children[1];
      return new Proxy(this, new MapRowProxyHandler());
    }
    [Symbol.iterator]() {
      return new MapRowIterator(this[kKeys], this[kVals]);
    }
    get size() {
      return this[kKeys].length;
    }
    toArray() {
      return Object.values(this.toJSON());
    }
    toJSON() {
      const keys = this[kKeys];
      const vals = this[kVals];
      const json = {};
      for (let i = -1, n = keys.length; ++i < n; ) {
        json[keys.get(i)] = instance2.visit(vals, i);
      }
      return json;
    }
    toString() {
      return `{${[...this].map(([key, val]) => `${valueToString(key)}: ${valueToString(val)}`).join(", ")}}`;
    }
    [Symbol.for("nodejs.util.inspect.custom")]() {
      return this.toString();
    }
  };
  var MapRowIterator = class {
    constructor(keys, vals) {
      this.keys = keys;
      this.vals = vals;
      this.keyIndex = 0;
      this.numKeys = keys.length;
    }
    [Symbol.iterator]() {
      return this;
    }
    next() {
      const i = this.keyIndex;
      if (i === this.numKeys) {
        return { done: true, value: null };
      }
      this.keyIndex++;
      return {
        done: false,
        value: [
          this.keys.get(i),
          instance2.visit(this.vals, i)
        ]
      };
    }
  };
  var MapRowProxyHandler = class {
    isExtensible() {
      return false;
    }
    deleteProperty() {
      return false;
    }
    preventExtensions() {
      return true;
    }
    ownKeys(row) {
      return row[kKeys].toArray().map(String);
    }
    has(row, key) {
      return row[kKeys].includes(key);
    }
    getOwnPropertyDescriptor(row, key) {
      const idx = row[kKeys].indexOf(key);
      if (idx !== -1) {
        return { writable: true, enumerable: true, configurable: true };
      }
      return;
    }
    get(row, key) {
      if (Reflect.has(row, key)) {
        return row[key];
      }
      const idx = row[kKeys].indexOf(key);
      if (idx !== -1) {
        const val = instance2.visit(Reflect.get(row, kVals), idx);
        Reflect.set(row, key, val);
        return val;
      }
    }
    set(row, key, val) {
      const idx = row[kKeys].indexOf(key);
      if (idx !== -1) {
        instance.visit(Reflect.get(row, kVals), idx, val);
        return Reflect.set(row, key, val);
      } else if (Reflect.has(row, key)) {
        return Reflect.set(row, key, val);
      }
      return false;
    }
  };
  Object.defineProperties(MapRow.prototype, {
    [Symbol.toStringTag]: { enumerable: false, configurable: false, value: "Row" },
    [kKeys]: { writable: true, enumerable: false, configurable: false, value: null },
    [kVals]: { writable: true, enumerable: false, configurable: false, value: null }
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/vector.mjs
  function clampIndex(source, index, then) {
    const length = source.length;
    const adjust = index > -1 ? index : length + index % length;
    return then ? then(source, adjust) : adjust;
  }
  var tmp;
  function clampRange(source, begin, end, then) {
    const { length: len = 0 } = source;
    let lhs = typeof begin !== "number" ? 0 : begin;
    let rhs = typeof end !== "number" ? len : end;
    lhs < 0 && (lhs = (lhs % len + len) % len);
    rhs < 0 && (rhs = (rhs % len + len) % len);
    rhs < lhs && (tmp = lhs, lhs = rhs, rhs = tmp);
    rhs > len && (rhs = len);
    return then ? then(source, lhs, rhs) : [lhs, rhs];
  }
  var isNaNFast = (value) => value !== value;
  function createElementComparator(search) {
    const typeofSearch = typeof search;
    if (typeofSearch !== "object" || search === null) {
      if (isNaNFast(search)) {
        return isNaNFast;
      }
      return (value) => value === search;
    }
    if (search instanceof Date) {
      const valueOfSearch = search.valueOf();
      return (value) => value instanceof Date ? value.valueOf() === valueOfSearch : false;
    }
    if (ArrayBuffer.isView(search)) {
      return (value) => value ? compareArrayLike(search, value) : false;
    }
    if (search instanceof Map) {
      return createMapComparator(search);
    }
    if (Array.isArray(search)) {
      return createArrayLikeComparator(search);
    }
    if (search instanceof Vector) {
      return createVectorComparator(search);
    }
    return createObjectComparator(search, true);
  }
  function createArrayLikeComparator(lhs) {
    const comparators = [];
    for (let i = -1, n = lhs.length; ++i < n; ) {
      comparators[i] = createElementComparator(lhs[i]);
    }
    return createSubElementsComparator(comparators);
  }
  function createMapComparator(lhs) {
    let i = -1;
    const comparators = [];
    for (const v of lhs.values())
      comparators[++i] = createElementComparator(v);
    return createSubElementsComparator(comparators);
  }
  function createVectorComparator(lhs) {
    const comparators = [];
    for (let i = -1, n = lhs.length; ++i < n; ) {
      comparators[i] = createElementComparator(lhs.get(i));
    }
    return createSubElementsComparator(comparators);
  }
  function createObjectComparator(lhs, allowEmpty = false) {
    const keys = Object.keys(lhs);
    if (!allowEmpty && keys.length === 0) {
      return () => false;
    }
    const comparators = [];
    for (let i = -1, n = keys.length; ++i < n; ) {
      comparators[i] = createElementComparator(lhs[keys[i]]);
    }
    return createSubElementsComparator(comparators, keys);
  }
  function createSubElementsComparator(comparators, keys) {
    return (rhs) => {
      if (!rhs || typeof rhs !== "object") {
        return false;
      }
      switch (rhs.constructor) {
        case Array:
          return compareArray(comparators, rhs);
        case Map:
          return compareObject(comparators, rhs, rhs.keys());
        case MapRow:
        case StructRow:
        case Object:
        case void 0:
          return compareObject(comparators, rhs, keys || Object.keys(rhs));
      }
      return rhs instanceof Vector ? compareVector(comparators, rhs) : false;
    };
  }
  function compareArray(comparators, arr) {
    const n = comparators.length;
    if (arr.length !== n) {
      return false;
    }
    for (let i = -1; ++i < n; ) {
      if (!comparators[i](arr[i])) {
        return false;
      }
    }
    return true;
  }
  function compareVector(comparators, vec) {
    const n = comparators.length;
    if (vec.length !== n) {
      return false;
    }
    for (let i = -1; ++i < n; ) {
      if (!comparators[i](vec.get(i))) {
        return false;
      }
    }
    return true;
  }
  function compareObject(comparators, obj, keys) {
    const lKeyItr = keys[Symbol.iterator]();
    const rKeyItr = obj instanceof Map ? obj.keys() : Object.keys(obj)[Symbol.iterator]();
    const rValItr = obj instanceof Map ? obj.values() : Object.values(obj)[Symbol.iterator]();
    let i = 0;
    const n = comparators.length;
    let rVal = rValItr.next();
    let lKey = lKeyItr.next();
    let rKey = rKeyItr.next();
    for (; i < n && !lKey.done && !rKey.done && !rVal.done; ++i, lKey = lKeyItr.next(), rKey = rKeyItr.next(), rVal = rValItr.next()) {
      if (lKey.value !== rKey.value || !comparators[i](rVal.value)) {
        break;
      }
    }
    if (i === n && lKey.done && rKey.done && rVal.done) {
      return true;
    }
    lKeyItr.return && lKeyItr.return();
    rKeyItr.return && rKeyItr.return();
    rValItr.return && rValItr.return();
    return false;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/bit.mjs
  var bit_exports = {};
  __export(bit_exports, {
    BitIterator: () => BitIterator,
    getBit: () => getBit,
    getBool: () => getBool2,
    packBools: () => packBools,
    popcnt_array: () => popcnt_array,
    popcnt_bit_range: () => popcnt_bit_range,
    popcnt_uint32: () => popcnt_uint32,
    setBool: () => setBool2,
    truncateBitmap: () => truncateBitmap
  });
  function getBool2(_data, _index, byte, bit) {
    return (byte & 1 << bit) !== 0;
  }
  function getBit(_data, _index, byte, bit) {
    return (byte & 1 << bit) >> bit;
  }
  function setBool2(bytes, index, value) {
    return value ? !!(bytes[index >> 3] |= 1 << index % 8) || true : !(bytes[index >> 3] &= ~(1 << index % 8)) && false;
  }
  function truncateBitmap(offset, length, bitmap) {
    const alignedSize = bitmap.byteLength + 7 & ~7;
    if (offset > 0 || bitmap.byteLength < alignedSize) {
      const bytes = new Uint8Array(alignedSize);
      bytes.set(offset % 8 === 0 ? bitmap.subarray(offset >> 3) : (
        // Otherwise iterate each bit from the offset and return a new one
        packBools(new BitIterator(bitmap, offset, length, null, getBool2)).subarray(0, alignedSize)
      ));
      return bytes;
    }
    return bitmap;
  }
  function packBools(values) {
    const xs = [];
    let i = 0, bit = 0, byte = 0;
    for (const value of values) {
      value && (byte |= 1 << bit);
      if (++bit === 8) {
        xs[i++] = byte;
        byte = bit = 0;
      }
    }
    if (i === 0 || bit > 0) {
      xs[i++] = byte;
    }
    const b = new Uint8Array(xs.length + 7 & ~7);
    b.set(xs);
    return b;
  }
  var BitIterator = class {
    constructor(bytes, begin, length, context, get) {
      this.bytes = bytes;
      this.length = length;
      this.context = context;
      this.get = get;
      this.bit = begin % 8;
      this.byteIndex = begin >> 3;
      this.byte = bytes[this.byteIndex++];
      this.index = 0;
    }
    next() {
      if (this.index < this.length) {
        if (this.bit === 8) {
          this.bit = 0;
          this.byte = this.bytes[this.byteIndex++];
        }
        return {
          value: this.get(this.context, this.index++, this.byte, this.bit++)
        };
      }
      return { done: true, value: null };
    }
    [Symbol.iterator]() {
      return this;
    }
  };
  function popcnt_bit_range(data, lhs, rhs) {
    if (rhs - lhs <= 0) {
      return 0;
    }
    if (rhs - lhs < 8) {
      let sum2 = 0;
      for (const bit of new BitIterator(data, lhs, rhs - lhs, data, getBit)) {
        sum2 += bit;
      }
      return sum2;
    }
    const rhsInside = rhs >> 3 << 3;
    const lhsInside = lhs + (lhs % 8 === 0 ? 0 : 8 - lhs % 8);
    return (
      // Get the popcnt of bits between the left hand side, and the next highest multiple of 8
      popcnt_bit_range(data, lhs, lhsInside) + // Get the popcnt of bits between the right hand side, and the next lowest multiple of 8
      popcnt_bit_range(data, rhsInside, rhs) + // Get the popcnt of all bits between the left and right hand sides' multiples of 8
      popcnt_array(data, lhsInside >> 3, rhsInside - lhsInside >> 3)
    );
  }
  function popcnt_array(arr, byteOffset, byteLength) {
    let cnt = 0, pos = Math.trunc(byteOffset);
    const view = new DataView(arr.buffer, arr.byteOffset, arr.byteLength);
    const len = byteLength === void 0 ? arr.byteLength : pos + byteLength;
    while (len - pos >= 4) {
      cnt += popcnt_uint32(view.getUint32(pos));
      pos += 4;
    }
    while (len - pos >= 2) {
      cnt += popcnt_uint32(view.getUint16(pos));
      pos += 2;
    }
    while (len - pos >= 1) {
      cnt += popcnt_uint32(view.getUint8(pos));
      pos += 1;
    }
    return cnt;
  }
  function popcnt_uint32(uint32) {
    let i = Math.trunc(uint32);
    i = i - (i >>> 1 & 1431655765);
    i = (i & 858993459) + (i >>> 2 & 858993459);
    return (i + (i >>> 4) & 252645135) * 16843009 >>> 24;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/data.mjs
  var kUnknownNullCount = -1;
  var Data = class _Data {
    constructor(type2, offset, length, nullCount, buffers, children = [], dictionary) {
      this.type = type2;
      this.children = children;
      this.dictionary = dictionary;
      this.offset = Math.floor(Math.max(offset || 0, 0));
      this.length = Math.floor(Math.max(length || 0, 0));
      this._nullCount = Math.floor(Math.max(nullCount || 0, -1));
      let buffer;
      if (buffers instanceof _Data) {
        this.stride = buffers.stride;
        this.values = buffers.values;
        this.typeIds = buffers.typeIds;
        this.nullBitmap = buffers.nullBitmap;
        this.valueOffsets = buffers.valueOffsets;
      } else {
        this.stride = strideForType(type2);
        if (buffers) {
          (buffer = buffers[0]) && (this.valueOffsets = buffer);
          (buffer = buffers[1]) && (this.values = buffer);
          (buffer = buffers[2]) && (this.nullBitmap = buffer);
          (buffer = buffers[3]) && (this.typeIds = buffer);
        }
      }
      this.nullable = this._nullCount !== 0 && this.nullBitmap && this.nullBitmap.byteLength > 0;
    }
    get typeId() {
      return this.type.typeId;
    }
    get ArrayType() {
      return this.type.ArrayType;
    }
    get buffers() {
      return [this.valueOffsets, this.values, this.nullBitmap, this.typeIds];
    }
    get byteLength() {
      let byteLength = 0;
      const { valueOffsets, values, nullBitmap, typeIds } = this;
      valueOffsets && (byteLength += valueOffsets.byteLength);
      values && (byteLength += values.byteLength);
      nullBitmap && (byteLength += nullBitmap.byteLength);
      typeIds && (byteLength += typeIds.byteLength);
      return this.children.reduce((byteLength2, child) => byteLength2 + child.byteLength, byteLength);
    }
    get nullCount() {
      let nullCount = this._nullCount;
      let nullBitmap;
      if (nullCount <= kUnknownNullCount && (nullBitmap = this.nullBitmap)) {
        this._nullCount = nullCount = this.length - popcnt_bit_range(nullBitmap, this.offset, this.offset + this.length);
      }
      return nullCount;
    }
    getValid(index) {
      if (this.nullable && this.nullCount > 0) {
        const pos = this.offset + index;
        const val = this.nullBitmap[pos >> 3];
        return (val & 1 << pos % 8) !== 0;
      }
      return true;
    }
    setValid(index, value) {
      if (!this.nullable) {
        return value;
      }
      if (!this.nullBitmap || this.nullBitmap.byteLength <= index >> 3) {
        const { nullBitmap: nullBitmap2 } = this._changeLengthAndBackfillNullBitmap(this.length);
        Object.assign(this, { nullBitmap: nullBitmap2, _nullCount: 0 });
      }
      const { nullBitmap, offset } = this;
      const pos = offset + index >> 3;
      const bit = (offset + index) % 8;
      const val = nullBitmap[pos] >> bit & 1;
      value ? val === 0 && (nullBitmap[pos] |= 1 << bit, this._nullCount = this.nullCount + 1) : val === 1 && (nullBitmap[pos] &= ~(1 << bit), this._nullCount = this.nullCount - 1);
      return value;
    }
    clone(type2 = this.type, offset = this.offset, length = this.length, nullCount = this._nullCount, buffers = this, children = this.children) {
      return new _Data(type2, offset, length, nullCount, buffers, children, this.dictionary);
    }
    slice(offset, length) {
      const { stride, typeId, children } = this;
      const nullCount = +(this._nullCount === 0) - 1;
      const childStride = typeId === 16 ? stride : 1;
      const buffers = this._sliceBuffers(offset, length, stride, typeId);
      return this.clone(
        this.type,
        this.offset + offset,
        length,
        nullCount,
        buffers,
        // Don't slice children if we have value offsets (the variable-width types)
        children.length === 0 || this.valueOffsets ? children : this._sliceChildren(children, childStride * offset, childStride * length)
      );
    }
    _changeLengthAndBackfillNullBitmap(newLength) {
      if (this.typeId === Type.Null) {
        return this.clone(this.type, 0, newLength, 0);
      }
      const { length, nullCount } = this;
      const bitmap = new Uint8Array((newLength + 63 & ~63) >> 3).fill(255, 0, length >> 3);
      bitmap[length >> 3] = (1 << length - (length & ~7)) - 1;
      if (nullCount > 0) {
        bitmap.set(truncateBitmap(this.offset, length, this.nullBitmap), 0);
      }
      const buffers = this.buffers;
      buffers[BufferType.VALIDITY] = bitmap;
      return this.clone(this.type, 0, newLength, nullCount + (newLength - length), buffers);
    }
    _sliceBuffers(offset, length, stride, typeId) {
      let arr;
      const { buffers } = this;
      (arr = buffers[BufferType.TYPE]) && (buffers[BufferType.TYPE] = arr.subarray(offset, offset + length));
      (arr = buffers[BufferType.OFFSET]) && (buffers[BufferType.OFFSET] = arr.subarray(offset, offset + length + 1)) || // Otherwise if no offsets, slice the data buffer. Don't slice the data vector for Booleans, since the offset goes by bits not bytes
      (arr = buffers[BufferType.DATA]) && (buffers[BufferType.DATA] = typeId === 6 ? arr : arr.subarray(stride * offset, stride * (offset + length)));
      return buffers;
    }
    _sliceChildren(children, offset, length) {
      return children.map((child) => child.slice(offset, length));
    }
  };
  Data.prototype.children = Object.freeze([]);
  var MakeDataVisitor = class _MakeDataVisitor extends Visitor {
    visit(props) {
      return this.getVisitFn(props["type"]).call(this, props);
    }
    visitNull(props) {
      const { ["type"]: type2, ["offset"]: offset = 0, ["length"]: length = 0 } = props;
      return new Data(type2, offset, length, 0);
    }
    visitBool(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length >> 3, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitInt(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitFloat(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitUtf8(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const data = toUint8Array(props["data"]);
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const valueOffsets = toInt32Array(props["valueOffsets"]);
      const { ["length"]: length = valueOffsets.length - 1, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [valueOffsets, data, nullBitmap]);
    }
    visitBinary(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const data = toUint8Array(props["data"]);
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const valueOffsets = toInt32Array(props["valueOffsets"]);
      const { ["length"]: length = valueOffsets.length - 1, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [valueOffsets, data, nullBitmap]);
    }
    visitFixedSizeBinary(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitDate(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitTimestamp(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitTime(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitDecimal(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitList(props) {
      const { ["type"]: type2, ["offset"]: offset = 0, ["child"]: child } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const valueOffsets = toInt32Array(props["valueOffsets"]);
      const { ["length"]: length = valueOffsets.length - 1, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [valueOffsets, void 0, nullBitmap], [child]);
    }
    visitStruct(props) {
      const { ["type"]: type2, ["offset"]: offset = 0, ["children"]: children = [] } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const { length = children.reduce((len, { length: length2 }) => Math.max(len, length2), 0), nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, void 0, nullBitmap], children);
    }
    visitUnion(props) {
      const { ["type"]: type2, ["offset"]: offset = 0, ["children"]: children = [] } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const typeIds = toArrayBufferView(type2.ArrayType, props["typeIds"]);
      const { ["length"]: length = typeIds.length, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      if (DataType.isSparseUnion(type2)) {
        return new Data(type2, offset, length, nullCount, [void 0, void 0, nullBitmap, typeIds], children);
      }
      const valueOffsets = toInt32Array(props["valueOffsets"]);
      return new Data(type2, offset, length, nullCount, [valueOffsets, void 0, nullBitmap, typeIds], children);
    }
    visitDictionary(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.indices.ArrayType, props["data"]);
      const { ["dictionary"]: dictionary = new Vector([new _MakeDataVisitor().visit({ type: type2.dictionary })]) } = props;
      const { ["length"]: length = data.length, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap], [], dictionary);
    }
    visitInterval(props) {
      const { ["type"]: type2, ["offset"]: offset = 0 } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const data = toArrayBufferView(type2.ArrayType, props["data"]);
      const { ["length"]: length = data.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, data, nullBitmap]);
    }
    visitFixedSizeList(props) {
      const { ["type"]: type2, ["offset"]: offset = 0, ["child"]: child = new _MakeDataVisitor().visit({ type: type2.valueType }) } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const { ["length"]: length = child.length / strideForType(type2), ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [void 0, void 0, nullBitmap], [child]);
    }
    visitMap(props) {
      const { ["type"]: type2, ["offset"]: offset = 0, ["child"]: child = new _MakeDataVisitor().visit({ type: type2.childType }) } = props;
      const nullBitmap = toUint8Array(props["nullBitmap"]);
      const valueOffsets = toInt32Array(props["valueOffsets"]);
      const { ["length"]: length = valueOffsets.length - 1, ["nullCount"]: nullCount = props["nullBitmap"] ? -1 : 0 } = props;
      return new Data(type2, offset, length, nullCount, [valueOffsets, void 0, nullBitmap], [child]);
    }
  };
  function makeData(props) {
    return new MakeDataVisitor().visit(props);
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/chunk.mjs
  var ChunkedIterator = class {
    constructor(numChunks = 0, getChunkIterator) {
      this.numChunks = numChunks;
      this.getChunkIterator = getChunkIterator;
      this.chunkIndex = 0;
      this.chunkIterator = this.getChunkIterator(0);
    }
    next() {
      while (this.chunkIndex < this.numChunks) {
        const next = this.chunkIterator.next();
        if (!next.done) {
          return next;
        }
        if (++this.chunkIndex < this.numChunks) {
          this.chunkIterator = this.getChunkIterator(this.chunkIndex);
        }
      }
      return { done: true, value: null };
    }
    [Symbol.iterator]() {
      return this;
    }
  };
  function computeChunkNullCounts(chunks) {
    return chunks.reduce((nullCount, chunk) => nullCount + chunk.nullCount, 0);
  }
  function computeChunkOffsets(chunks) {
    return chunks.reduce((offsets, chunk, index) => {
      offsets[index + 1] = offsets[index] + chunk.length;
      return offsets;
    }, new Uint32Array(chunks.length + 1));
  }
  function sliceChunks(chunks, offsets, begin, end) {
    const slices = [];
    for (let i = -1, n = chunks.length; ++i < n; ) {
      const chunk = chunks[i];
      const offset = offsets[i];
      const { length } = chunk;
      if (offset >= end) {
        break;
      }
      if (begin >= offset + length) {
        continue;
      }
      if (offset >= begin && offset + length <= end) {
        slices.push(chunk);
        continue;
      }
      const from = Math.max(0, begin - offset);
      const to = Math.min(end - offset, length);
      slices.push(chunk.slice(from, to - from));
    }
    if (slices.length === 0) {
      slices.push(chunks[0].slice(0, 0));
    }
    return slices;
  }
  function binarySearch(chunks, offsets, idx, fn) {
    let lhs = 0, mid = 0, rhs = offsets.length - 1;
    do {
      if (lhs >= rhs - 1) {
        return idx < offsets[rhs] ? fn(chunks, lhs, idx - offsets[lhs]) : null;
      }
      mid = lhs + Math.trunc((rhs - lhs) * 0.5);
      idx < offsets[mid] ? rhs = mid : lhs = mid;
    } while (lhs < rhs);
  }
  function isChunkedValid(data, index) {
    return data.getValid(index);
  }
  function wrapChunkedCall1(fn) {
    function chunkedFn(chunks, i, j) {
      return fn(chunks[i], j);
    }
    return function(index) {
      const data = this.data;
      return binarySearch(data, this._offsets, index, chunkedFn);
    };
  }
  function wrapChunkedCall2(fn) {
    let _2;
    function chunkedFn(chunks, i, j) {
      return fn(chunks[i], j, _2);
    }
    return function(index, value) {
      const data = this.data;
      _2 = value;
      const result = binarySearch(data, this._offsets, index, chunkedFn);
      _2 = void 0;
      return result;
    };
  }
  function wrapChunkedIndexOf(indexOf) {
    let _1;
    function chunkedIndexOf(data, chunkIndex, fromIndex) {
      let begin = fromIndex, index = 0, total = 0;
      for (let i = chunkIndex - 1, n = data.length; ++i < n; ) {
        const chunk = data[i];
        if (~(index = indexOf(chunk, _1, begin))) {
          return total + index;
        }
        begin = 0;
        total += chunk.length;
      }
      return -1;
    }
    return function(element, offset) {
      _1 = element;
      const data = this.data;
      const result = typeof offset !== "number" ? chunkedIndexOf(data, 0, 0) : binarySearch(data, this._offsets, offset, chunkedIndexOf);
      _1 = void 0;
      return result;
    };
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/indexof.mjs
  var IndexOfVisitor = class extends Visitor {
  };
  function nullIndexOf(data, searchElement) {
    return searchElement === null && data.length > 0 ? 0 : -1;
  }
  function indexOfNull(data, fromIndex) {
    const { nullBitmap } = data;
    if (!nullBitmap || data.nullCount <= 0) {
      return -1;
    }
    let i = 0;
    for (const isValid of new BitIterator(nullBitmap, data.offset + (fromIndex || 0), data.length, nullBitmap, getBool2)) {
      if (!isValid) {
        return i;
      }
      ++i;
    }
    return -1;
  }
  function indexOfValue(data, searchElement, fromIndex) {
    if (searchElement === void 0) {
      return -1;
    }
    if (searchElement === null) {
      return indexOfNull(data, fromIndex);
    }
    const get = instance2.getVisitFn(data);
    const compare = createElementComparator(searchElement);
    for (let i = (fromIndex || 0) - 1, n = data.length; ++i < n; ) {
      if (compare(get(data, i))) {
        return i;
      }
    }
    return -1;
  }
  function indexOfUnion(data, searchElement, fromIndex) {
    const get = instance2.getVisitFn(data);
    const compare = createElementComparator(searchElement);
    for (let i = (fromIndex || 0) - 1, n = data.length; ++i < n; ) {
      if (compare(get(data, i))) {
        return i;
      }
    }
    return -1;
  }
  IndexOfVisitor.prototype.visitNull = nullIndexOf;
  IndexOfVisitor.prototype.visitBool = indexOfValue;
  IndexOfVisitor.prototype.visitInt = indexOfValue;
  IndexOfVisitor.prototype.visitInt8 = indexOfValue;
  IndexOfVisitor.prototype.visitInt16 = indexOfValue;
  IndexOfVisitor.prototype.visitInt32 = indexOfValue;
  IndexOfVisitor.prototype.visitInt64 = indexOfValue;
  IndexOfVisitor.prototype.visitUint8 = indexOfValue;
  IndexOfVisitor.prototype.visitUint16 = indexOfValue;
  IndexOfVisitor.prototype.visitUint32 = indexOfValue;
  IndexOfVisitor.prototype.visitUint64 = indexOfValue;
  IndexOfVisitor.prototype.visitFloat = indexOfValue;
  IndexOfVisitor.prototype.visitFloat16 = indexOfValue;
  IndexOfVisitor.prototype.visitFloat32 = indexOfValue;
  IndexOfVisitor.prototype.visitFloat64 = indexOfValue;
  IndexOfVisitor.prototype.visitUtf8 = indexOfValue;
  IndexOfVisitor.prototype.visitBinary = indexOfValue;
  IndexOfVisitor.prototype.visitFixedSizeBinary = indexOfValue;
  IndexOfVisitor.prototype.visitDate = indexOfValue;
  IndexOfVisitor.prototype.visitDateDay = indexOfValue;
  IndexOfVisitor.prototype.visitDateMillisecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimestamp = indexOfValue;
  IndexOfVisitor.prototype.visitTimestampSecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimestampMillisecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimestampMicrosecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimestampNanosecond = indexOfValue;
  IndexOfVisitor.prototype.visitTime = indexOfValue;
  IndexOfVisitor.prototype.visitTimeSecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimeMillisecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimeMicrosecond = indexOfValue;
  IndexOfVisitor.prototype.visitTimeNanosecond = indexOfValue;
  IndexOfVisitor.prototype.visitDecimal = indexOfValue;
  IndexOfVisitor.prototype.visitList = indexOfValue;
  IndexOfVisitor.prototype.visitStruct = indexOfValue;
  IndexOfVisitor.prototype.visitUnion = indexOfValue;
  IndexOfVisitor.prototype.visitDenseUnion = indexOfUnion;
  IndexOfVisitor.prototype.visitSparseUnion = indexOfUnion;
  IndexOfVisitor.prototype.visitDictionary = indexOfValue;
  IndexOfVisitor.prototype.visitInterval = indexOfValue;
  IndexOfVisitor.prototype.visitIntervalDayTime = indexOfValue;
  IndexOfVisitor.prototype.visitIntervalYearMonth = indexOfValue;
  IndexOfVisitor.prototype.visitFixedSizeList = indexOfValue;
  IndexOfVisitor.prototype.visitMap = indexOfValue;
  var instance3 = new IndexOfVisitor();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/iterator.mjs
  var IteratorVisitor = class extends Visitor {
  };
  function vectorIterator(vector) {
    const { type: type2 } = vector;
    if (vector.nullCount === 0 && vector.stride === 1 && (type2.typeId === Type.Timestamp || type2 instanceof Int_ && type2.bitWidth !== 64 || type2 instanceof Time_ && type2.bitWidth !== 64 || type2 instanceof Float && type2.precision !== Precision.HALF)) {
      return new ChunkedIterator(vector.data.length, (chunkIndex) => {
        const data = vector.data[chunkIndex];
        return data.values.subarray(0, data.length)[Symbol.iterator]();
      });
    }
    let offset = 0;
    return new ChunkedIterator(vector.data.length, (chunkIndex) => {
      const data = vector.data[chunkIndex];
      const length = data.length;
      const inner = vector.slice(offset, offset + length);
      offset += length;
      return new VectorIterator(inner);
    });
  }
  var VectorIterator = class {
    constructor(vector) {
      this.vector = vector;
      this.index = 0;
    }
    next() {
      if (this.index < this.vector.length) {
        return {
          value: this.vector.get(this.index++)
        };
      }
      return { done: true, value: null };
    }
    [Symbol.iterator]() {
      return this;
    }
  };
  IteratorVisitor.prototype.visitNull = vectorIterator;
  IteratorVisitor.prototype.visitBool = vectorIterator;
  IteratorVisitor.prototype.visitInt = vectorIterator;
  IteratorVisitor.prototype.visitInt8 = vectorIterator;
  IteratorVisitor.prototype.visitInt16 = vectorIterator;
  IteratorVisitor.prototype.visitInt32 = vectorIterator;
  IteratorVisitor.prototype.visitInt64 = vectorIterator;
  IteratorVisitor.prototype.visitUint8 = vectorIterator;
  IteratorVisitor.prototype.visitUint16 = vectorIterator;
  IteratorVisitor.prototype.visitUint32 = vectorIterator;
  IteratorVisitor.prototype.visitUint64 = vectorIterator;
  IteratorVisitor.prototype.visitFloat = vectorIterator;
  IteratorVisitor.prototype.visitFloat16 = vectorIterator;
  IteratorVisitor.prototype.visitFloat32 = vectorIterator;
  IteratorVisitor.prototype.visitFloat64 = vectorIterator;
  IteratorVisitor.prototype.visitUtf8 = vectorIterator;
  IteratorVisitor.prototype.visitBinary = vectorIterator;
  IteratorVisitor.prototype.visitFixedSizeBinary = vectorIterator;
  IteratorVisitor.prototype.visitDate = vectorIterator;
  IteratorVisitor.prototype.visitDateDay = vectorIterator;
  IteratorVisitor.prototype.visitDateMillisecond = vectorIterator;
  IteratorVisitor.prototype.visitTimestamp = vectorIterator;
  IteratorVisitor.prototype.visitTimestampSecond = vectorIterator;
  IteratorVisitor.prototype.visitTimestampMillisecond = vectorIterator;
  IteratorVisitor.prototype.visitTimestampMicrosecond = vectorIterator;
  IteratorVisitor.prototype.visitTimestampNanosecond = vectorIterator;
  IteratorVisitor.prototype.visitTime = vectorIterator;
  IteratorVisitor.prototype.visitTimeSecond = vectorIterator;
  IteratorVisitor.prototype.visitTimeMillisecond = vectorIterator;
  IteratorVisitor.prototype.visitTimeMicrosecond = vectorIterator;
  IteratorVisitor.prototype.visitTimeNanosecond = vectorIterator;
  IteratorVisitor.prototype.visitDecimal = vectorIterator;
  IteratorVisitor.prototype.visitList = vectorIterator;
  IteratorVisitor.prototype.visitStruct = vectorIterator;
  IteratorVisitor.prototype.visitUnion = vectorIterator;
  IteratorVisitor.prototype.visitDenseUnion = vectorIterator;
  IteratorVisitor.prototype.visitSparseUnion = vectorIterator;
  IteratorVisitor.prototype.visitDictionary = vectorIterator;
  IteratorVisitor.prototype.visitInterval = vectorIterator;
  IteratorVisitor.prototype.visitIntervalDayTime = vectorIterator;
  IteratorVisitor.prototype.visitIntervalYearMonth = vectorIterator;
  IteratorVisitor.prototype.visitFixedSizeList = vectorIterator;
  IteratorVisitor.prototype.visitMap = vectorIterator;
  var instance4 = new IteratorVisitor();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/bytelength.mjs
  var sum = (x, y) => x + y;
  var GetByteLengthVisitor = class extends Visitor {
    visitNull(____, _) {
      return 0;
    }
    visitInt(data, _) {
      return data.type.bitWidth / 8;
    }
    visitFloat(data, _) {
      return data.type.ArrayType.BYTES_PER_ELEMENT;
    }
    visitBool(____, _) {
      return 1 / 8;
    }
    visitDecimal(data, _) {
      return data.type.bitWidth / 8;
    }
    visitDate(data, _) {
      return (data.type.unit + 1) * 4;
    }
    visitTime(data, _) {
      return data.type.bitWidth / 8;
    }
    visitTimestamp(data, _) {
      return data.type.unit === TimeUnit.SECOND ? 4 : 8;
    }
    visitInterval(data, _) {
      return (data.type.unit + 1) * 4;
    }
    visitStruct(data, i) {
      return data.children.reduce((total, child) => total + instance5.visit(child, i), 0);
    }
    visitFixedSizeBinary(data, _) {
      return data.type.byteWidth;
    }
    visitMap(data, i) {
      return 8 + data.children.reduce((total, child) => total + instance5.visit(child, i), 0);
    }
    visitDictionary(data, i) {
      var _a5;
      return data.type.indices.bitWidth / 8 + (((_a5 = data.dictionary) === null || _a5 === void 0 ? void 0 : _a5.getByteLength(data.values[i])) || 0);
    }
  };
  var getUtf8ByteLength = ({ valueOffsets }, index) => {
    return 8 + (valueOffsets[index + 1] - valueOffsets[index]);
  };
  var getBinaryByteLength = ({ valueOffsets }, index) => {
    return 8 + (valueOffsets[index + 1] - valueOffsets[index]);
  };
  var getListByteLength = ({ valueOffsets, stride, children }, index) => {
    const child = children[0];
    const { [index * stride]: start } = valueOffsets;
    const { [index * stride + 1]: end } = valueOffsets;
    const visit = instance5.getVisitFn(child.type);
    const slice = child.slice(start, end - start);
    let size = 8;
    for (let idx = -1, len = end - start; ++idx < len; ) {
      size += visit(slice, idx);
    }
    return size;
  };
  var getFixedSizeListByteLength = ({ stride, children }, index) => {
    const child = children[0];
    const slice = child.slice(index * stride, stride);
    const visit = instance5.getVisitFn(child.type);
    let size = 0;
    for (let idx = -1, len = slice.length; ++idx < len; ) {
      size += visit(slice, idx);
    }
    return size;
  };
  var getUnionByteLength = (data, index) => {
    return data.type.mode === UnionMode.Dense ? getDenseUnionByteLength(data, index) : getSparseUnionByteLength(data, index);
  };
  var getDenseUnionByteLength = ({ type: type2, children, typeIds, valueOffsets }, index) => {
    const childIndex = type2.typeIdToChildIndex[typeIds[index]];
    return 8 + instance5.visit(children[childIndex], valueOffsets[index]);
  };
  var getSparseUnionByteLength = ({ children }, index) => {
    return 4 + instance5.visitMany(children, children.map(() => index)).reduce(sum, 0);
  };
  GetByteLengthVisitor.prototype.visitUtf8 = getUtf8ByteLength;
  GetByteLengthVisitor.prototype.visitBinary = getBinaryByteLength;
  GetByteLengthVisitor.prototype.visitList = getListByteLength;
  GetByteLengthVisitor.prototype.visitFixedSizeList = getFixedSizeListByteLength;
  GetByteLengthVisitor.prototype.visitUnion = getUnionByteLength;
  GetByteLengthVisitor.prototype.visitDenseUnion = getDenseUnionByteLength;
  GetByteLengthVisitor.prototype.visitSparseUnion = getSparseUnionByteLength;
  var instance5 = new GetByteLengthVisitor();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/vector.mjs
  var _a2;
  var visitorsByTypeId = {};
  var vectorPrototypesByTypeId = {};
  var Vector = class _Vector {
    constructor(input) {
      var _b2, _c2, _d2;
      const data = input[0] instanceof _Vector ? input.flatMap((x) => x.data) : input;
      if (data.length === 0 || data.some((x) => !(x instanceof Data))) {
        throw new TypeError("Vector constructor expects an Array of Data instances.");
      }
      const type2 = (_b2 = data[0]) === null || _b2 === void 0 ? void 0 : _b2.type;
      switch (data.length) {
        case 0:
          this._offsets = [0];
          break;
        case 1: {
          const { get, set, indexOf, byteLength } = visitorsByTypeId[type2.typeId];
          const unchunkedData = data[0];
          this.isValid = (index) => isChunkedValid(unchunkedData, index);
          this.get = (index) => get(unchunkedData, index);
          this.set = (index, value) => set(unchunkedData, index, value);
          this.indexOf = (index) => indexOf(unchunkedData, index);
          this.getByteLength = (index) => byteLength(unchunkedData, index);
          this._offsets = [0, unchunkedData.length];
          break;
        }
        default:
          Object.setPrototypeOf(this, vectorPrototypesByTypeId[type2.typeId]);
          this._offsets = computeChunkOffsets(data);
          break;
      }
      this.data = data;
      this.type = type2;
      this.stride = strideForType(type2);
      this.numChildren = (_d2 = (_c2 = type2.children) === null || _c2 === void 0 ? void 0 : _c2.length) !== null && _d2 !== void 0 ? _d2 : 0;
      this.length = this._offsets[this._offsets.length - 1];
    }
    /**
     * The aggregate size (in bytes) of this Vector's buffers and/or child Vectors.
     */
    get byteLength() {
      if (this._byteLength === -1) {
        this._byteLength = this.data.reduce((byteLength, data) => byteLength + data.byteLength, 0);
      }
      return this._byteLength;
    }
    /**
     * The number of null elements in this Vector.
     */
    get nullCount() {
      if (this._nullCount === -1) {
        this._nullCount = computeChunkNullCounts(this.data);
      }
      return this._nullCount;
    }
    /**
     * The Array or TypedAray constructor used for the JS representation
     *  of the element's values in {@link Vector.prototype.toArray `toArray()`}.
     */
    get ArrayType() {
      return this.type.ArrayType;
    }
    /**
     * The name that should be printed when the Vector is logged in a message.
     */
    get [Symbol.toStringTag]() {
      return `${this.VectorName}<${this.type[Symbol.toStringTag]}>`;
    }
    /**
     * The name of this Vector.
     */
    get VectorName() {
      return `${Type[this.type.typeId]}Vector`;
    }
    /**
     * Check whether an element is null.
     * @param index The index at which to read the validity bitmap.
     */
    // @ts-ignore
    isValid(index) {
      return false;
    }
    /**
     * Get an element value by position.
     * @param index The index of the element to read.
     */
    // @ts-ignore
    get(index) {
      return null;
    }
    /**
     * Set an element value by position.
     * @param index The index of the element to write.
     * @param value The value to set.
     */
    // @ts-ignore
    set(index, value) {
      return;
    }
    /**
     * Retrieve the index of the first occurrence of a value in an Vector.
     * @param element The value to locate in the Vector.
     * @param offset The index at which to begin the search. If offset is omitted, the search starts at index 0.
     */
    // @ts-ignore
    indexOf(element, offset) {
      return -1;
    }
    includes(element, offset) {
      return this.indexOf(element, offset) > 0;
    }
    /**
     * Get the size in bytes of an element by index.
     * @param index The index at which to get the byteLength.
     */
    // @ts-ignore
    getByteLength(index) {
      return 0;
    }
    /**
     * Iterator for the Vector's elements.
     */
    [Symbol.iterator]() {
      return instance4.visit(this);
    }
    /**
     * Combines two or more Vectors of the same type.
     * @param others Additional Vectors to add to the end of this Vector.
     */
    concat(...others) {
      return new _Vector(this.data.concat(others.flatMap((x) => x.data).flat(Number.POSITIVE_INFINITY)));
    }
    /**
     * Return a zero-copy sub-section of this Vector.
     * @param start The beginning of the specified portion of the Vector.
     * @param end The end of the specified portion of the Vector. This is exclusive of the element at the index 'end'.
     */
    slice(begin, end) {
      return new _Vector(clampRange(this, begin, end, ({ data, _offsets }, begin2, end2) => sliceChunks(data, _offsets, begin2, end2)));
    }
    toJSON() {
      return [...this];
    }
    /**
     * Return a JavaScript Array or TypedArray of the Vector's elements.
     *
     * @note If this Vector contains a single Data chunk and the Vector's type is a
     *  primitive numeric type corresponding to one of the JavaScript TypedArrays, this
     *  method returns a zero-copy slice of the underlying TypedArray values. If there's
     *  more than one chunk, the resulting TypedArray will be a copy of the data from each
     *  chunk's underlying TypedArray values.
     *
     * @returns An Array or TypedArray of the Vector's elements, based on the Vector's DataType.
     */
    toArray() {
      const { type: type2, data, length, stride, ArrayType } = this;
      switch (type2.typeId) {
        case Type.Int:
        case Type.Float:
        case Type.Decimal:
        case Type.Time:
        case Type.Timestamp:
          switch (data.length) {
            case 0:
              return new ArrayType();
            case 1:
              return data[0].values.subarray(0, length * stride);
            default:
              return data.reduce((memo, { values, length: chunk_length }) => {
                memo.array.set(values.subarray(0, chunk_length * stride), memo.offset);
                memo.offset += chunk_length * stride;
                return memo;
              }, { array: new ArrayType(length * stride), offset: 0 }).array;
          }
      }
      return [...this];
    }
    /**
     * Returns a string representation of the Vector.
     *
     * @returns A string representation of the Vector.
     */
    toString() {
      return `[${[...this].join(",")}]`;
    }
    /**
     * Returns a child Vector by name, or null if this Vector has no child with the given name.
     * @param name The name of the child to retrieve.
     */
    getChild(name) {
      var _b2;
      return this.getChildAt((_b2 = this.type.children) === null || _b2 === void 0 ? void 0 : _b2.findIndex((f) => f.name === name));
    }
    /**
     * Returns a child Vector by index, or null if this Vector has no child at the supplied index.
     * @param index The index of the child to retrieve.
     */
    getChildAt(index) {
      if (index > -1 && index < this.numChildren) {
        return new _Vector(this.data.map(({ children }) => children[index]));
      }
      return null;
    }
    get isMemoized() {
      if (DataType.isDictionary(this.type)) {
        return this.data[0].dictionary.isMemoized;
      }
      return false;
    }
    /**
     * Adds memoization to the Vector's {@link get} method. For dictionary
     * vectors, this method return a vector that memoizes only the dictionary
     * values.
     *
     * Memoization is very useful when decoding a value is expensive such as
     * Uft8. The memoization creates a cache of the size of the Vector and
     * therfore increases memory usage.
     *
     * @returns A new vector that memoizes calls to {@link get}.
     */
    memoize() {
      if (DataType.isDictionary(this.type)) {
        const dictionary = new MemoizedVector(this.data[0].dictionary);
        const newData = this.data.map((data) => {
          const cloned = data.clone();
          cloned.dictionary = dictionary;
          return cloned;
        });
        return new _Vector(newData);
      }
      return new MemoizedVector(this);
    }
    /**
     * Returns a vector without memoization of the {@link get} method. If this
     * vector is not memoized, this method returns this vector.
     *
     * @returns A a vector without memoization.
     */
    unmemoize() {
      if (DataType.isDictionary(this.type) && this.isMemoized) {
        const dictionary = this.data[0].dictionary.unmemoize();
        const newData = this.data.map((data) => {
          const newData2 = data.clone();
          newData2.dictionary = dictionary;
          return newData2;
        });
        return new _Vector(newData);
      }
      return this;
    }
  };
  _a2 = Symbol.toStringTag;
  Vector[_a2] = ((proto) => {
    proto.type = DataType.prototype;
    proto.data = [];
    proto.length = 0;
    proto.stride = 1;
    proto.numChildren = 0;
    proto._nullCount = -1;
    proto._byteLength = -1;
    proto._offsets = new Uint32Array([0]);
    proto[Symbol.isConcatSpreadable] = true;
    const typeIds = Object.keys(Type).map((T) => Type[T]).filter((T) => typeof T === "number" && T !== Type.NONE);
    for (const typeId of typeIds) {
      const get = instance2.getVisitFnByTypeId(typeId);
      const set = instance.getVisitFnByTypeId(typeId);
      const indexOf = instance3.getVisitFnByTypeId(typeId);
      const byteLength = instance5.getVisitFnByTypeId(typeId);
      visitorsByTypeId[typeId] = { get, set, indexOf, byteLength };
      vectorPrototypesByTypeId[typeId] = Object.create(proto, {
        ["isValid"]: { value: wrapChunkedCall1(isChunkedValid) },
        ["get"]: { value: wrapChunkedCall1(instance2.getVisitFnByTypeId(typeId)) },
        ["set"]: { value: wrapChunkedCall2(instance.getVisitFnByTypeId(typeId)) },
        ["indexOf"]: { value: wrapChunkedIndexOf(instance3.getVisitFnByTypeId(typeId)) },
        ["getByteLength"]: { value: wrapChunkedCall1(instance5.getVisitFnByTypeId(typeId)) }
      });
    }
    return "Vector";
  })(Vector.prototype);
  var MemoizedVector = class _MemoizedVector extends Vector {
    constructor(vector) {
      super(vector.data);
      const get = this.get;
      const set = this.set;
      const slice = this.slice;
      const cache = new Array(this.length);
      Object.defineProperty(this, "get", {
        value(index) {
          const cachedValue = cache[index];
          if (cachedValue !== void 0) {
            return cachedValue;
          }
          const value = get.call(this, index);
          cache[index] = value;
          return value;
        }
      });
      Object.defineProperty(this, "set", {
        value(index, value) {
          set.call(this, index, value);
          cache[index] = value;
        }
      });
      Object.defineProperty(this, "slice", {
        value: (begin, end) => new _MemoizedVector(slice.call(this, begin, end))
      });
      Object.defineProperty(this, "isMemoized", { value: true });
      Object.defineProperty(this, "unmemoize", {
        value: () => new Vector(this.data)
      });
      Object.defineProperty(this, "memoize", {
        value: () => this
      });
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/valid.mjs
  function createIsValidFunction(nullValues) {
    if (!nullValues || nullValues.length <= 0) {
      return function isValid(value) {
        return true;
      };
    }
    let fnBody = "";
    const noNaNs = nullValues.filter((x) => x === x);
    if (noNaNs.length > 0) {
      fnBody = `
    switch (x) {${noNaNs.map((x) => `
        case ${valueToCase(x)}:`).join("")}
            return false;
    }`;
    }
    if (nullValues.length !== noNaNs.length) {
      fnBody = `if (x !== x) return false;
${fnBody}`;
    }
    return new Function(`x`, `${fnBody}
return true;`);
  }
  function valueToCase(x) {
    if (typeof x !== "bigint") {
      return valueToString(x);
    } else if (BigIntAvailable) {
      return `${valueToString(x)}n`;
    }
    return `"${valueToString(x)}"`;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/buffer.mjs
  var roundLengthUpToNearest64Bytes = (len, BPE) => (Math.ceil(len) * BPE + 63 & ~63 || 64) / BPE;
  var sliceOrExtendArray = (arr, len = 0) => arr.length >= len ? arr.subarray(0, len) : memcpy(new arr.constructor(len), arr, 0);
  var BufferBuilder = class {
    constructor(buffer, stride = 1) {
      this.buffer = buffer;
      this.stride = stride;
      this.BYTES_PER_ELEMENT = buffer.BYTES_PER_ELEMENT;
      this.ArrayType = buffer.constructor;
      this._resize(this.length = Math.ceil(buffer.length / stride));
    }
    get byteLength() {
      return Math.ceil(this.length * this.stride) * this.BYTES_PER_ELEMENT;
    }
    get reservedLength() {
      return this.buffer.length / this.stride;
    }
    get reservedByteLength() {
      return this.buffer.byteLength;
    }
    // @ts-ignore
    set(index, value) {
      return this;
    }
    append(value) {
      return this.set(this.length, value);
    }
    reserve(extra) {
      if (extra > 0) {
        this.length += extra;
        const stride = this.stride;
        const length = this.length * stride;
        const reserved = this.buffer.length;
        if (length >= reserved) {
          this._resize(reserved === 0 ? roundLengthUpToNearest64Bytes(length * 1, this.BYTES_PER_ELEMENT) : roundLengthUpToNearest64Bytes(length * 2, this.BYTES_PER_ELEMENT));
        }
      }
      return this;
    }
    flush(length = this.length) {
      length = roundLengthUpToNearest64Bytes(length * this.stride, this.BYTES_PER_ELEMENT);
      const array = sliceOrExtendArray(this.buffer, length);
      this.clear();
      return array;
    }
    clear() {
      this.length = 0;
      this._resize(0);
      return this;
    }
    _resize(newLength) {
      return this.buffer = memcpy(new this.ArrayType(newLength), this.buffer);
    }
  };
  BufferBuilder.prototype.offset = 0;
  var DataBufferBuilder = class extends BufferBuilder {
    last() {
      return this.get(this.length - 1);
    }
    get(index) {
      return this.buffer[index];
    }
    set(index, value) {
      this.reserve(index - this.length + 1);
      this.buffer[index * this.stride] = value;
      return this;
    }
  };
  var BitmapBufferBuilder = class extends DataBufferBuilder {
    constructor(data = new Uint8Array(0)) {
      super(data, 1 / 8);
      this.numValid = 0;
    }
    get numInvalid() {
      return this.length - this.numValid;
    }
    get(idx) {
      return this.buffer[idx >> 3] >> idx % 8 & 1;
    }
    set(idx, val) {
      const { buffer } = this.reserve(idx - this.length + 1);
      const byte = idx >> 3, bit = idx % 8, cur = buffer[byte] >> bit & 1;
      val ? cur === 0 && (buffer[byte] |= 1 << bit, ++this.numValid) : cur === 1 && (buffer[byte] &= ~(1 << bit), --this.numValid);
      return this;
    }
    clear() {
      this.numValid = 0;
      return super.clear();
    }
  };
  var OffsetsBufferBuilder = class extends DataBufferBuilder {
    constructor(data = new Int32Array(1)) {
      super(data, 1);
    }
    append(value) {
      return this.set(this.length - 1, value);
    }
    set(index, value) {
      const offset = this.length - 1;
      const buffer = this.reserve(index - offset + 1).buffer;
      if (offset < index++) {
        buffer.fill(buffer[offset], offset, index);
      }
      buffer[index] = buffer[index - 1] + value;
      return this;
    }
    flush(length = this.length - 1) {
      if (length > this.length) {
        this.set(length - 1, 0);
      }
      return super.flush(length + 1);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder.mjs
  var Builder = class {
    /**
     * Construct a builder with the given Arrow DataType with optional null values,
     * which will be interpreted as "null" when set or appended to the `Builder`.
     * @param {{ type: T, nullValues?: any[] }} options A `BuilderOptions` object used to create this `Builder`.
     */
    constructor({ "type": type2, "nullValues": nulls }) {
      this.length = 0;
      this.finished = false;
      this.type = type2;
      this.children = [];
      this.nullValues = nulls;
      this.stride = strideForType(type2);
      this._nulls = new BitmapBufferBuilder();
      if (nulls && nulls.length > 0) {
        this._isValid = createIsValidFunction(nulls);
      }
    }
    /** @nocollapse */
    // @ts-ignore
    static throughNode(options) {
      throw new Error(`"throughNode" not available in this environment`);
    }
    /** @nocollapse */
    // @ts-ignore
    static throughDOM(options) {
      throw new Error(`"throughDOM" not available in this environment`);
    }
    /**
     * Flush the `Builder` and return a `Vector<T>`.
     * @returns {Vector<T>} A `Vector<T>` of the flushed values.
     */
    toVector() {
      return new Vector([this.flush()]);
    }
    get ArrayType() {
      return this.type.ArrayType;
    }
    get nullCount() {
      return this._nulls.numInvalid;
    }
    get numChildren() {
      return this.children.length;
    }
    /**
     * @returns The aggregate length (in bytes) of the values that have been written.
     */
    get byteLength() {
      let size = 0;
      const { _offsets, _values, _nulls, _typeIds, children } = this;
      _offsets && (size += _offsets.byteLength);
      _values && (size += _values.byteLength);
      _nulls && (size += _nulls.byteLength);
      _typeIds && (size += _typeIds.byteLength);
      return children.reduce((size2, child) => size2 + child.byteLength, size);
    }
    /**
     * @returns The aggregate number of rows that have been reserved to write new values.
     */
    get reservedLength() {
      return this._nulls.reservedLength;
    }
    /**
     * @returns The aggregate length (in bytes) that has been reserved to write new values.
     */
    get reservedByteLength() {
      let size = 0;
      this._offsets && (size += this._offsets.reservedByteLength);
      this._values && (size += this._values.reservedByteLength);
      this._nulls && (size += this._nulls.reservedByteLength);
      this._typeIds && (size += this._typeIds.reservedByteLength);
      return this.children.reduce((size2, child) => size2 + child.reservedByteLength, size);
    }
    get valueOffsets() {
      return this._offsets ? this._offsets.buffer : null;
    }
    get values() {
      return this._values ? this._values.buffer : null;
    }
    get nullBitmap() {
      return this._nulls ? this._nulls.buffer : null;
    }
    get typeIds() {
      return this._typeIds ? this._typeIds.buffer : null;
    }
    /**
     * Appends a value (or null) to this `Builder`.
     * This is equivalent to `builder.set(builder.length, value)`.
     * @param {T['TValue'] | TNull } value The value to append.
     */
    append(value) {
      return this.set(this.length, value);
    }
    /**
     * Validates whether a value is valid (true), or null (false)
     * @param {T['TValue'] | TNull } value The value to compare against null the value representations
     */
    isValid(value) {
      return this._isValid(value);
    }
    /**
     * Write a value (or null-value sentinel) at the supplied index.
     * If the value matches one of the null-value representations, a 1-bit is
     * written to the null `BitmapBufferBuilder`. Otherwise, a 0 is written to
     * the null `BitmapBufferBuilder`, and the value is passed to
     * `Builder.prototype.setValue()`.
     * @param {number} index The index of the value to write.
     * @param {T['TValue'] | TNull } value The value to write at the supplied index.
     * @returns {this} The updated `Builder` instance.
     */
    set(index, value) {
      if (this.setValid(index, this.isValid(value))) {
        this.setValue(index, value);
      }
      return this;
    }
    /**
     * Write a value to the underlying buffers at the supplied index, bypassing
     * the null-value check. This is a low-level method that
     * @param {number} index
     * @param {T['TValue'] | TNull } value
     */
    setValue(index, value) {
      this._setValue(this, index, value);
    }
    setValid(index, valid) {
      this.length = this._nulls.set(index, +valid).length;
      return valid;
    }
    // @ts-ignore
    addChild(child, name = `${this.numChildren}`) {
      throw new Error(`Cannot append children to non-nested type "${this.type}"`);
    }
    /**
     * Retrieve the child `Builder` at the supplied `index`, or null if no child
     * exists at that index.
     * @param {number} index The index of the child `Builder` to retrieve.
     * @returns {Builder | null} The child Builder at the supplied index or null.
     */
    getChildAt(index) {
      return this.children[index] || null;
    }
    /**
     * Commit all the values that have been written to their underlying
     * ArrayBuffers, including any child Builders if applicable, and reset
     * the internal `Builder` state.
     * @returns A `Data<T>` of the buffers and children representing the values written.
     */
    flush() {
      let data;
      let typeIds;
      let nullBitmap;
      let valueOffsets;
      const { type: type2, length, nullCount, _typeIds, _offsets, _values, _nulls } = this;
      if (typeIds = _typeIds === null || _typeIds === void 0 ? void 0 : _typeIds.flush(length)) {
        valueOffsets = _offsets === null || _offsets === void 0 ? void 0 : _offsets.flush(length);
      } else if (valueOffsets = _offsets === null || _offsets === void 0 ? void 0 : _offsets.flush(length)) {
        data = _values === null || _values === void 0 ? void 0 : _values.flush(_offsets.last());
      } else {
        data = _values === null || _values === void 0 ? void 0 : _values.flush(length);
      }
      if (nullCount > 0) {
        nullBitmap = _nulls === null || _nulls === void 0 ? void 0 : _nulls.flush(length);
      }
      const children = this.children.map((child) => child.flush());
      this.clear();
      return makeData({
        type: type2,
        length,
        nullCount,
        children,
        "child": children[0],
        data,
        typeIds,
        nullBitmap,
        valueOffsets
      });
    }
    /**
     * Finalize this `Builder`, and child builders if applicable.
     * @returns {this} The finalized `Builder` instance.
     */
    finish() {
      this.finished = true;
      for (const child of this.children)
        child.finish();
      return this;
    }
    /**
     * Clear this Builder's internal state, including child Builders if applicable, and reset the length to 0.
     * @returns {this} The cleared `Builder` instance.
     */
    clear() {
      var _a5, _b2, _c2, _d2;
      this.length = 0;
      (_a5 = this._nulls) === null || _a5 === void 0 ? void 0 : _a5.clear();
      (_b2 = this._values) === null || _b2 === void 0 ? void 0 : _b2.clear();
      (_c2 = this._offsets) === null || _c2 === void 0 ? void 0 : _c2.clear();
      (_d2 = this._typeIds) === null || _d2 === void 0 ? void 0 : _d2.clear();
      for (const child of this.children)
        child.clear();
      return this;
    }
  };
  Builder.prototype.length = 1;
  Builder.prototype.stride = 1;
  Builder.prototype.children = null;
  Builder.prototype.finished = false;
  Builder.prototype.nullValues = null;
  Builder.prototype._isValid = () => true;
  var FixedWidthBuilder = class extends Builder {
    constructor(opts) {
      super(opts);
      this._values = new DataBufferBuilder(new this.ArrayType(0), this.stride);
    }
    setValue(index, value) {
      const values = this._values;
      values.reserve(index - values.length + 1);
      return super.setValue(index, value);
    }
  };
  var VariableWidthBuilder = class extends Builder {
    constructor(opts) {
      super(opts);
      this._pendingLength = 0;
      this._offsets = new OffsetsBufferBuilder();
    }
    setValue(index, value) {
      const pending = this._pending || (this._pending = /* @__PURE__ */ new Map());
      const current = pending.get(index);
      current && (this._pendingLength -= current.length);
      this._pendingLength += value instanceof MapRow ? value[kKeys].length : value.length;
      pending.set(index, value);
    }
    setValid(index, isValid) {
      if (!super.setValid(index, isValid)) {
        (this._pending || (this._pending = /* @__PURE__ */ new Map())).set(index, void 0);
        return false;
      }
      return true;
    }
    clear() {
      this._pendingLength = 0;
      this._pending = void 0;
      return super.clear();
    }
    flush() {
      this._flush();
      return super.flush();
    }
    finish() {
      this._flush();
      return super.finish();
    }
    _flush() {
      const pending = this._pending;
      const pendingLength = this._pendingLength;
      this._pendingLength = 0;
      this._pending = void 0;
      if (pending && pending.size > 0) {
        this._flushPending(pending, pendingLength);
      }
      return this;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/block.mjs
  var Block = class {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    /**
     * Index to the start of the RecordBlock (note this is past the Message header)
     */
    offset() {
      return this.bb.readInt64(this.bb_pos);
    }
    /**
     * Length of the metadata
     */
    metaDataLength() {
      return this.bb.readInt32(this.bb_pos + 8);
    }
    /**
     * Length of the data (this is aligned so there can be a gap between this and
     * the metadata).
     */
    bodyLength() {
      return this.bb.readInt64(this.bb_pos + 16);
    }
    static sizeOf() {
      return 24;
    }
    static createBlock(builder, offset, metaDataLength, bodyLength) {
      builder.prep(8, 24);
      builder.writeInt64(bodyLength);
      builder.pad(4);
      builder.writeInt32(metaDataLength);
      builder.writeInt64(offset);
      return builder.offset();
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/flatbuffers/mjs/constants.js
  var SIZEOF_SHORT = 2;
  var SIZEOF_INT = 4;
  var FILE_IDENTIFIER_LENGTH = 4;
  var SIZE_PREFIX_LENGTH = 4;

  // ../../../../../tmp/agrolattice_component_build/node_modules/flatbuffers/mjs/utils.js
  var int32 = new Int32Array(2);
  var float32 = new Float32Array(int32.buffer);
  var float64 = new Float64Array(int32.buffer);
  var isLittleEndian = new Uint16Array(new Uint8Array([1, 0]).buffer)[0] === 1;

  // ../../../../../tmp/agrolattice_component_build/node_modules/flatbuffers/mjs/long.js
  var Long = class _Long {
    constructor(low, high) {
      this.low = low | 0;
      this.high = high | 0;
    }
    static create(low, high) {
      return low == 0 && high == 0 ? _Long.ZERO : new _Long(low, high);
    }
    toFloat64() {
      return (this.low >>> 0) + this.high * 4294967296;
    }
    equals(other) {
      return this.low == other.low && this.high == other.high;
    }
  };
  Long.ZERO = new Long(0, 0);

  // ../../../../../tmp/agrolattice_component_build/node_modules/flatbuffers/mjs/encoding.js
  var Encoding;
  (function(Encoding2) {
    Encoding2[Encoding2["UTF8_BYTES"] = 1] = "UTF8_BYTES";
    Encoding2[Encoding2["UTF16_STRING"] = 2] = "UTF16_STRING";
  })(Encoding || (Encoding = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/flatbuffers/mjs/byte-buffer.js
  var ByteBuffer = class _ByteBuffer {
    /**
     * Create a new ByteBuffer with a given array of bytes (`Uint8Array`)
     */
    constructor(bytes_) {
      this.bytes_ = bytes_;
      this.position_ = 0;
    }
    /**
     * Create and allocate a new ByteBuffer with a given size.
     */
    static allocate(byte_size) {
      return new _ByteBuffer(new Uint8Array(byte_size));
    }
    clear() {
      this.position_ = 0;
    }
    /**
     * Get the underlying `Uint8Array`.
     */
    bytes() {
      return this.bytes_;
    }
    /**
     * Get the buffer's position.
     */
    position() {
      return this.position_;
    }
    /**
     * Set the buffer's position.
     */
    setPosition(position) {
      this.position_ = position;
    }
    /**
     * Get the buffer's capacity.
     */
    capacity() {
      return this.bytes_.length;
    }
    readInt8(offset) {
      return this.readUint8(offset) << 24 >> 24;
    }
    readUint8(offset) {
      return this.bytes_[offset];
    }
    readInt16(offset) {
      return this.readUint16(offset) << 16 >> 16;
    }
    readUint16(offset) {
      return this.bytes_[offset] | this.bytes_[offset + 1] << 8;
    }
    readInt32(offset) {
      return this.bytes_[offset] | this.bytes_[offset + 1] << 8 | this.bytes_[offset + 2] << 16 | this.bytes_[offset + 3] << 24;
    }
    readUint32(offset) {
      return this.readInt32(offset) >>> 0;
    }
    readInt64(offset) {
      return new Long(this.readInt32(offset), this.readInt32(offset + 4));
    }
    readUint64(offset) {
      return new Long(this.readUint32(offset), this.readUint32(offset + 4));
    }
    readFloat32(offset) {
      int32[0] = this.readInt32(offset);
      return float32[0];
    }
    readFloat64(offset) {
      int32[isLittleEndian ? 0 : 1] = this.readInt32(offset);
      int32[isLittleEndian ? 1 : 0] = this.readInt32(offset + 4);
      return float64[0];
    }
    writeInt8(offset, value) {
      this.bytes_[offset] = value;
    }
    writeUint8(offset, value) {
      this.bytes_[offset] = value;
    }
    writeInt16(offset, value) {
      this.bytes_[offset] = value;
      this.bytes_[offset + 1] = value >> 8;
    }
    writeUint16(offset, value) {
      this.bytes_[offset] = value;
      this.bytes_[offset + 1] = value >> 8;
    }
    writeInt32(offset, value) {
      this.bytes_[offset] = value;
      this.bytes_[offset + 1] = value >> 8;
      this.bytes_[offset + 2] = value >> 16;
      this.bytes_[offset + 3] = value >> 24;
    }
    writeUint32(offset, value) {
      this.bytes_[offset] = value;
      this.bytes_[offset + 1] = value >> 8;
      this.bytes_[offset + 2] = value >> 16;
      this.bytes_[offset + 3] = value >> 24;
    }
    writeInt64(offset, value) {
      this.writeInt32(offset, value.low);
      this.writeInt32(offset + 4, value.high);
    }
    writeUint64(offset, value) {
      this.writeUint32(offset, value.low);
      this.writeUint32(offset + 4, value.high);
    }
    writeFloat32(offset, value) {
      float32[0] = value;
      this.writeInt32(offset, int32[0]);
    }
    writeFloat64(offset, value) {
      float64[0] = value;
      this.writeInt32(offset, int32[isLittleEndian ? 0 : 1]);
      this.writeInt32(offset + 4, int32[isLittleEndian ? 1 : 0]);
    }
    /**
     * Return the file identifier.   Behavior is undefined for FlatBuffers whose
     * schema does not include a file_identifier (likely points at padding or the
     * start of a the root vtable).
     */
    getBufferIdentifier() {
      if (this.bytes_.length < this.position_ + SIZEOF_INT + FILE_IDENTIFIER_LENGTH) {
        throw new Error("FlatBuffers: ByteBuffer is too short to contain an identifier.");
      }
      let result = "";
      for (let i = 0; i < FILE_IDENTIFIER_LENGTH; i++) {
        result += String.fromCharCode(this.readInt8(this.position_ + SIZEOF_INT + i));
      }
      return result;
    }
    /**
     * Look up a field in the vtable, return an offset into the object, or 0 if the
     * field is not present.
     */
    __offset(bb_pos, vtable_offset) {
      const vtable = bb_pos - this.readInt32(bb_pos);
      return vtable_offset < this.readInt16(vtable) ? this.readInt16(vtable + vtable_offset) : 0;
    }
    /**
     * Initialize any Table-derived type to point to the union at the given offset.
     */
    __union(t, offset) {
      t.bb_pos = offset + this.readInt32(offset);
      t.bb = this;
      return t;
    }
    /**
     * Create a JavaScript string from UTF-8 data stored inside the FlatBuffer.
     * This allocates a new string and converts to wide chars upon each access.
     *
     * To avoid the conversion to UTF-16, pass Encoding.UTF8_BYTES as
     * the "optionalEncoding" argument. This is useful for avoiding conversion to
     * and from UTF-16 when the data will just be packaged back up in another
     * FlatBuffer later on.
     *
     * @param offset
     * @param opt_encoding Defaults to UTF16_STRING
     */
    __string(offset, opt_encoding) {
      offset += this.readInt32(offset);
      const length = this.readInt32(offset);
      let result = "";
      let i = 0;
      offset += SIZEOF_INT;
      if (opt_encoding === Encoding.UTF8_BYTES) {
        return this.bytes_.subarray(offset, offset + length);
      }
      while (i < length) {
        let codePoint;
        const a = this.readUint8(offset + i++);
        if (a < 192) {
          codePoint = a;
        } else {
          const b = this.readUint8(offset + i++);
          if (a < 224) {
            codePoint = (a & 31) << 6 | b & 63;
          } else {
            const c = this.readUint8(offset + i++);
            if (a < 240) {
              codePoint = (a & 15) << 12 | (b & 63) << 6 | c & 63;
            } else {
              const d = this.readUint8(offset + i++);
              codePoint = (a & 7) << 18 | (b & 63) << 12 | (c & 63) << 6 | d & 63;
            }
          }
        }
        if (codePoint < 65536) {
          result += String.fromCharCode(codePoint);
        } else {
          codePoint -= 65536;
          result += String.fromCharCode((codePoint >> 10) + 55296, (codePoint & (1 << 10) - 1) + 56320);
        }
      }
      return result;
    }
    /**
     * Handle unions that can contain string as its member, if a Table-derived type then initialize it,
     * if a string then return a new one
     *
     * WARNING: strings are immutable in JS so we can't change the string that the user gave us, this
     * makes the behaviour of __union_with_string different compared to __union
     */
    __union_with_string(o, offset) {
      if (typeof o === "string") {
        return this.__string(offset);
      }
      return this.__union(o, offset);
    }
    /**
     * Retrieve the relative offset stored at "offset"
     */
    __indirect(offset) {
      return offset + this.readInt32(offset);
    }
    /**
     * Get the start of data of a vector whose offset is stored at "offset" in this object.
     */
    __vector(offset) {
      return offset + this.readInt32(offset) + SIZEOF_INT;
    }
    /**
     * Get the length of a vector whose offset is stored at "offset" in this object.
     */
    __vector_len(offset) {
      return this.readInt32(offset + this.readInt32(offset));
    }
    __has_identifier(ident) {
      if (ident.length != FILE_IDENTIFIER_LENGTH) {
        throw new Error("FlatBuffers: file identifier must be length " + FILE_IDENTIFIER_LENGTH);
      }
      for (let i = 0; i < FILE_IDENTIFIER_LENGTH; i++) {
        if (ident.charCodeAt(i) != this.readInt8(this.position() + SIZEOF_INT + i)) {
          return false;
        }
      }
      return true;
    }
    /**
     * A helper function to avoid generated code depending on this file directly.
     */
    createLong(low, high) {
      return Long.create(low, high);
    }
    /**
     * A helper function for generating list for obj api
     */
    createScalarList(listAccessor, listLength) {
      const ret = [];
      for (let i = 0; i < listLength; ++i) {
        if (listAccessor(i) !== null) {
          ret.push(listAccessor(i));
        }
      }
      return ret;
    }
    /**
     * A helper function for generating list for obj api
     * @param listAccessor function that accepts an index and return data at that index
     * @param listLength listLength
     * @param res result list
     */
    createObjList(listAccessor, listLength) {
      const ret = [];
      for (let i = 0; i < listLength; ++i) {
        const val = listAccessor(i);
        if (val !== null) {
          ret.push(val.unpack());
        }
      }
      return ret;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/flatbuffers/mjs/builder.js
  var Builder2 = class _Builder {
    /**
     * Create a FlatBufferBuilder.
     */
    constructor(opt_initial_size) {
      this.minalign = 1;
      this.vtable = null;
      this.vtable_in_use = 0;
      this.isNested = false;
      this.object_start = 0;
      this.vtables = [];
      this.vector_num_elems = 0;
      this.force_defaults = false;
      this.string_maps = null;
      let initial_size;
      if (!opt_initial_size) {
        initial_size = 1024;
      } else {
        initial_size = opt_initial_size;
      }
      this.bb = ByteBuffer.allocate(initial_size);
      this.space = initial_size;
    }
    clear() {
      this.bb.clear();
      this.space = this.bb.capacity();
      this.minalign = 1;
      this.vtable = null;
      this.vtable_in_use = 0;
      this.isNested = false;
      this.object_start = 0;
      this.vtables = [];
      this.vector_num_elems = 0;
      this.force_defaults = false;
      this.string_maps = null;
    }
    /**
     * In order to save space, fields that are set to their default value
     * don't get serialized into the buffer. Forcing defaults provides a
     * way to manually disable this optimization.
     *
     * @param forceDefaults true always serializes default values
     */
    forceDefaults(forceDefaults) {
      this.force_defaults = forceDefaults;
    }
    /**
     * Get the ByteBuffer representing the FlatBuffer. Only call this after you've
     * called finish(). The actual data starts at the ByteBuffer's current position,
     * not necessarily at 0.
     */
    dataBuffer() {
      return this.bb;
    }
    /**
     * Get the bytes representing the FlatBuffer. Only call this after you've
     * called finish().
     */
    asUint8Array() {
      return this.bb.bytes().subarray(this.bb.position(), this.bb.position() + this.offset());
    }
    /**
     * Prepare to write an element of `size` after `additional_bytes` have been
     * written, e.g. if you write a string, you need to align such the int length
     * field is aligned to 4 bytes, and the string data follows it directly. If all
     * you need to do is alignment, `additional_bytes` will be 0.
     *
     * @param size This is the of the new element to write
     * @param additional_bytes The padding size
     */
    prep(size, additional_bytes) {
      if (size > this.minalign) {
        this.minalign = size;
      }
      const align_size = ~(this.bb.capacity() - this.space + additional_bytes) + 1 & size - 1;
      while (this.space < align_size + size + additional_bytes) {
        const old_buf_size = this.bb.capacity();
        this.bb = _Builder.growByteBuffer(this.bb);
        this.space += this.bb.capacity() - old_buf_size;
      }
      this.pad(align_size);
    }
    pad(byte_size) {
      for (let i = 0; i < byte_size; i++) {
        this.bb.writeInt8(--this.space, 0);
      }
    }
    writeInt8(value) {
      this.bb.writeInt8(this.space -= 1, value);
    }
    writeInt16(value) {
      this.bb.writeInt16(this.space -= 2, value);
    }
    writeInt32(value) {
      this.bb.writeInt32(this.space -= 4, value);
    }
    writeInt64(value) {
      this.bb.writeInt64(this.space -= 8, value);
    }
    writeFloat32(value) {
      this.bb.writeFloat32(this.space -= 4, value);
    }
    writeFloat64(value) {
      this.bb.writeFloat64(this.space -= 8, value);
    }
    /**
     * Add an `int8` to the buffer, properly aligned, and grows the buffer (if necessary).
     * @param value The `int8` to add the the buffer.
     */
    addInt8(value) {
      this.prep(1, 0);
      this.writeInt8(value);
    }
    /**
     * Add an `int16` to the buffer, properly aligned, and grows the buffer (if necessary).
     * @param value The `int16` to add the the buffer.
     */
    addInt16(value) {
      this.prep(2, 0);
      this.writeInt16(value);
    }
    /**
     * Add an `int32` to the buffer, properly aligned, and grows the buffer (if necessary).
     * @param value The `int32` to add the the buffer.
     */
    addInt32(value) {
      this.prep(4, 0);
      this.writeInt32(value);
    }
    /**
     * Add an `int64` to the buffer, properly aligned, and grows the buffer (if necessary).
     * @param value The `int64` to add the the buffer.
     */
    addInt64(value) {
      this.prep(8, 0);
      this.writeInt64(value);
    }
    /**
     * Add a `float32` to the buffer, properly aligned, and grows the buffer (if necessary).
     * @param value The `float32` to add the the buffer.
     */
    addFloat32(value) {
      this.prep(4, 0);
      this.writeFloat32(value);
    }
    /**
     * Add a `float64` to the buffer, properly aligned, and grows the buffer (if necessary).
     * @param value The `float64` to add the the buffer.
     */
    addFloat64(value) {
      this.prep(8, 0);
      this.writeFloat64(value);
    }
    addFieldInt8(voffset, value, defaultValue) {
      if (this.force_defaults || value != defaultValue) {
        this.addInt8(value);
        this.slot(voffset);
      }
    }
    addFieldInt16(voffset, value, defaultValue) {
      if (this.force_defaults || value != defaultValue) {
        this.addInt16(value);
        this.slot(voffset);
      }
    }
    addFieldInt32(voffset, value, defaultValue) {
      if (this.force_defaults || value != defaultValue) {
        this.addInt32(value);
        this.slot(voffset);
      }
    }
    addFieldInt64(voffset, value, defaultValue) {
      if (this.force_defaults || !value.equals(defaultValue)) {
        this.addInt64(value);
        this.slot(voffset);
      }
    }
    addFieldFloat32(voffset, value, defaultValue) {
      if (this.force_defaults || value != defaultValue) {
        this.addFloat32(value);
        this.slot(voffset);
      }
    }
    addFieldFloat64(voffset, value, defaultValue) {
      if (this.force_defaults || value != defaultValue) {
        this.addFloat64(value);
        this.slot(voffset);
      }
    }
    addFieldOffset(voffset, value, defaultValue) {
      if (this.force_defaults || value != defaultValue) {
        this.addOffset(value);
        this.slot(voffset);
      }
    }
    /**
     * Structs are stored inline, so nothing additional is being added. `d` is always 0.
     */
    addFieldStruct(voffset, value, defaultValue) {
      if (value != defaultValue) {
        this.nested(value);
        this.slot(voffset);
      }
    }
    /**
     * Structures are always stored inline, they need to be created right
     * where they're used.  You'll get this assertion failure if you
     * created it elsewhere.
     */
    nested(obj) {
      if (obj != this.offset()) {
        throw new Error("FlatBuffers: struct must be serialized inline.");
      }
    }
    /**
     * Should not be creating any other object, string or vector
     * while an object is being constructed
     */
    notNested() {
      if (this.isNested) {
        throw new Error("FlatBuffers: object serialization must not be nested.");
      }
    }
    /**
     * Set the current vtable at `voffset` to the current location in the buffer.
     */
    slot(voffset) {
      if (this.vtable !== null)
        this.vtable[voffset] = this.offset();
    }
    /**
     * @returns Offset relative to the end of the buffer.
     */
    offset() {
      return this.bb.capacity() - this.space;
    }
    /**
     * Doubles the size of the backing ByteBuffer and copies the old data towards
     * the end of the new buffer (since we build the buffer backwards).
     *
     * @param bb The current buffer with the existing data
     * @returns A new byte buffer with the old data copied
     * to it. The data is located at the end of the buffer.
     *
     * uint8Array.set() formally takes {Array<number>|ArrayBufferView}, so to pass
     * it a uint8Array we need to suppress the type check:
     * @suppress {checkTypes}
     */
    static growByteBuffer(bb) {
      const old_buf_size = bb.capacity();
      if (old_buf_size & 3221225472) {
        throw new Error("FlatBuffers: cannot grow buffer beyond 2 gigabytes.");
      }
      const new_buf_size = old_buf_size << 1;
      const nbb = ByteBuffer.allocate(new_buf_size);
      nbb.setPosition(new_buf_size - old_buf_size);
      nbb.bytes().set(bb.bytes(), new_buf_size - old_buf_size);
      return nbb;
    }
    /**
     * Adds on offset, relative to where it will be written.
     *
     * @param offset The offset to add.
     */
    addOffset(offset) {
      this.prep(SIZEOF_INT, 0);
      this.writeInt32(this.offset() - offset + SIZEOF_INT);
    }
    /**
     * Start encoding a new object in the buffer.  Users will not usually need to
     * call this directly. The FlatBuffers compiler will generate helper methods
     * that call this method internally.
     */
    startObject(numfields) {
      this.notNested();
      if (this.vtable == null) {
        this.vtable = [];
      }
      this.vtable_in_use = numfields;
      for (let i = 0; i < numfields; i++) {
        this.vtable[i] = 0;
      }
      this.isNested = true;
      this.object_start = this.offset();
    }
    /**
     * Finish off writing the object that is under construction.
     *
     * @returns The offset to the object inside `dataBuffer`
     */
    endObject() {
      if (this.vtable == null || !this.isNested) {
        throw new Error("FlatBuffers: endObject called without startObject");
      }
      this.addInt32(0);
      const vtableloc = this.offset();
      let i = this.vtable_in_use - 1;
      for (; i >= 0 && this.vtable[i] == 0; i--) {
      }
      const trimmed_size = i + 1;
      for (; i >= 0; i--) {
        this.addInt16(this.vtable[i] != 0 ? vtableloc - this.vtable[i] : 0);
      }
      const standard_fields = 2;
      this.addInt16(vtableloc - this.object_start);
      const len = (trimmed_size + standard_fields) * SIZEOF_SHORT;
      this.addInt16(len);
      let existing_vtable = 0;
      const vt1 = this.space;
      outer_loop: for (i = 0; i < this.vtables.length; i++) {
        const vt2 = this.bb.capacity() - this.vtables[i];
        if (len == this.bb.readInt16(vt2)) {
          for (let j = SIZEOF_SHORT; j < len; j += SIZEOF_SHORT) {
            if (this.bb.readInt16(vt1 + j) != this.bb.readInt16(vt2 + j)) {
              continue outer_loop;
            }
          }
          existing_vtable = this.vtables[i];
          break;
        }
      }
      if (existing_vtable) {
        this.space = this.bb.capacity() - vtableloc;
        this.bb.writeInt32(this.space, existing_vtable - vtableloc);
      } else {
        this.vtables.push(this.offset());
        this.bb.writeInt32(this.bb.capacity() - vtableloc, this.offset() - vtableloc);
      }
      this.isNested = false;
      return vtableloc;
    }
    /**
     * Finalize a buffer, poiting to the given `root_table`.
     */
    finish(root_table, opt_file_identifier, opt_size_prefix) {
      const size_prefix = opt_size_prefix ? SIZE_PREFIX_LENGTH : 0;
      if (opt_file_identifier) {
        const file_identifier = opt_file_identifier;
        this.prep(this.minalign, SIZEOF_INT + FILE_IDENTIFIER_LENGTH + size_prefix);
        if (file_identifier.length != FILE_IDENTIFIER_LENGTH) {
          throw new Error("FlatBuffers: file identifier must be length " + FILE_IDENTIFIER_LENGTH);
        }
        for (let i = FILE_IDENTIFIER_LENGTH - 1; i >= 0; i--) {
          this.writeInt8(file_identifier.charCodeAt(i));
        }
      }
      this.prep(this.minalign, SIZEOF_INT + size_prefix);
      this.addOffset(root_table);
      if (size_prefix) {
        this.addInt32(this.bb.capacity() - this.space);
      }
      this.bb.setPosition(this.space);
    }
    /**
     * Finalize a size prefixed buffer, pointing to the given `root_table`.
     */
    finishSizePrefixed(root_table, opt_file_identifier) {
      this.finish(root_table, opt_file_identifier, true);
    }
    /**
     * This checks a required field has been set in a given table that has
     * just been constructed.
     */
    requiredField(table, field) {
      const table_start = this.bb.capacity() - table;
      const vtable_start = table_start - this.bb.readInt32(table_start);
      const ok = this.bb.readInt16(vtable_start + field) != 0;
      if (!ok) {
        throw new Error("FlatBuffers: field " + field + " must be set");
      }
    }
    /**
     * Start a new array/vector of objects.  Users usually will not call
     * this directly. The FlatBuffers compiler will create a start/end
     * method for vector types in generated code.
     *
     * @param elem_size The size of each element in the array
     * @param num_elems The number of elements in the array
     * @param alignment The alignment of the array
     */
    startVector(elem_size, num_elems, alignment) {
      this.notNested();
      this.vector_num_elems = num_elems;
      this.prep(SIZEOF_INT, elem_size * num_elems);
      this.prep(alignment, elem_size * num_elems);
    }
    /**
     * Finish off the creation of an array and all its elements. The array must be
     * created with `startVector`.
     *
     * @returns The offset at which the newly created array
     * starts.
     */
    endVector() {
      this.writeInt32(this.vector_num_elems);
      return this.offset();
    }
    /**
     * Encode the string `s` in the buffer using UTF-8. If the string passed has
     * already been seen, we return the offset of the already written string
     *
     * @param s The string to encode
     * @return The offset in the buffer where the encoded string starts
     */
    createSharedString(s) {
      if (!s) {
        return 0;
      }
      if (!this.string_maps) {
        this.string_maps = /* @__PURE__ */ new Map();
      }
      if (this.string_maps.has(s)) {
        return this.string_maps.get(s);
      }
      const offset = this.createString(s);
      this.string_maps.set(s, offset);
      return offset;
    }
    /**
     * Encode the string `s` in the buffer using UTF-8. If a Uint8Array is passed
     * instead of a string, it is assumed to contain valid UTF-8 encoded data.
     *
     * @param s The string to encode
     * @return The offset in the buffer where the encoded string starts
     */
    createString(s) {
      if (!s) {
        return 0;
      }
      let utf8;
      if (s instanceof Uint8Array) {
        utf8 = s;
      } else {
        utf8 = [];
        let i = 0;
        while (i < s.length) {
          let codePoint;
          const a = s.charCodeAt(i++);
          if (a < 55296 || a >= 56320) {
            codePoint = a;
          } else {
            const b = s.charCodeAt(i++);
            codePoint = (a << 10) + b + (65536 - (55296 << 10) - 56320);
          }
          if (codePoint < 128) {
            utf8.push(codePoint);
          } else {
            if (codePoint < 2048) {
              utf8.push(codePoint >> 6 & 31 | 192);
            } else {
              if (codePoint < 65536) {
                utf8.push(codePoint >> 12 & 15 | 224);
              } else {
                utf8.push(codePoint >> 18 & 7 | 240, codePoint >> 12 & 63 | 128);
              }
              utf8.push(codePoint >> 6 & 63 | 128);
            }
            utf8.push(codePoint & 63 | 128);
          }
        }
      }
      this.addInt8(0);
      this.startVector(1, utf8.length, 1);
      this.bb.setPosition(this.space -= utf8.length);
      for (let i = 0, offset = this.space, bytes = this.bb.bytes(); i < utf8.length; i++) {
        bytes[offset++] = utf8[i];
      }
      return this.endVector();
    }
    /**
     * A helper function to avoid generated code depending on this file directly.
     */
    createLong(low, high) {
      return Long.create(low, high);
    }
    /**
     * A helper function to pack an object
     *
     * @returns offset of obj
     */
    createObjectOffset(obj) {
      if (obj === null) {
        return 0;
      }
      if (typeof obj === "string") {
        return this.createString(obj);
      } else {
        return obj.pack(this);
      }
    }
    /**
     * A helper function to pack a list of object
     *
     * @returns list of offsets of each non null object
     */
    createObjectOffsetList(list) {
      const ret = [];
      for (let i = 0; i < list.length; ++i) {
        const val = list[i];
        if (val !== null) {
          ret.push(this.createObjectOffset(val));
        } else {
          throw new Error("FlatBuffers: Argument for createObjectOffsetList cannot contain null.");
        }
      }
      return ret;
    }
    createStructOffsetList(list, startFunc) {
      startFunc(this, list.length);
      this.createObjectOffsetList(list);
      return this.endVector();
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/key-value.mjs
  var KeyValue = class _KeyValue {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsKeyValue(bb, obj) {
      return (obj || new _KeyValue()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsKeyValue(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _KeyValue()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    key(optionalEncoding) {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.__string(this.bb_pos + offset, optionalEncoding) : null;
    }
    value(optionalEncoding) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.__string(this.bb_pos + offset, optionalEncoding) : null;
    }
    static startKeyValue(builder) {
      builder.startObject(2);
    }
    static addKey(builder, keyOffset) {
      builder.addFieldOffset(0, keyOffset, 0);
    }
    static addValue(builder, valueOffset) {
      builder.addFieldOffset(1, valueOffset, 0);
    }
    static endKeyValue(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createKeyValue(builder, keyOffset, valueOffset) {
      _KeyValue.startKeyValue(builder);
      _KeyValue.addKey(builder, keyOffset);
      _KeyValue.addValue(builder, valueOffset);
      return _KeyValue.endKeyValue(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/metadata-version.mjs
  var MetadataVersion2;
  (function(MetadataVersion3) {
    MetadataVersion3[MetadataVersion3["V1"] = 0] = "V1";
    MetadataVersion3[MetadataVersion3["V2"] = 1] = "V2";
    MetadataVersion3[MetadataVersion3["V3"] = 2] = "V3";
    MetadataVersion3[MetadataVersion3["V4"] = 3] = "V4";
    MetadataVersion3[MetadataVersion3["V5"] = 4] = "V5";
  })(MetadataVersion2 || (MetadataVersion2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/endianness.mjs
  var Endianness;
  (function(Endianness2) {
    Endianness2[Endianness2["Little"] = 0] = "Little";
    Endianness2[Endianness2["Big"] = 1] = "Big";
  })(Endianness || (Endianness = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/dictionary-kind.mjs
  var DictionaryKind;
  (function(DictionaryKind2) {
    DictionaryKind2[DictionaryKind2["DenseArray"] = 0] = "DenseArray";
  })(DictionaryKind || (DictionaryKind = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/int.mjs
  var Int = class _Int {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsInt(bb, obj) {
      return (obj || new _Int()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsInt(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Int()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    bitWidth() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
    }
    isSigned() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? !!this.bb.readInt8(this.bb_pos + offset) : false;
    }
    static startInt(builder) {
      builder.startObject(2);
    }
    static addBitWidth(builder, bitWidth) {
      builder.addFieldInt32(0, bitWidth, 0);
    }
    static addIsSigned(builder, isSigned) {
      builder.addFieldInt8(1, +isSigned, 0);
    }
    static endInt(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createInt(builder, bitWidth, isSigned) {
      _Int.startInt(builder);
      _Int.addBitWidth(builder, bitWidth);
      _Int.addIsSigned(builder, isSigned);
      return _Int.endInt(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/dictionary-encoding.mjs
  var DictionaryEncoding = class _DictionaryEncoding {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsDictionaryEncoding(bb, obj) {
      return (obj || new _DictionaryEncoding()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsDictionaryEncoding(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _DictionaryEncoding()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * The known dictionary id in the application where this data is used. In
     * the file or streaming formats, the dictionary ids are found in the
     * DictionaryBatch messages
     */
    id() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt64(this.bb_pos + offset) : this.bb.createLong(0, 0);
    }
    /**
     * The dictionary indices are constrained to be non-negative integers. If
     * this field is null, the indices must be signed int32. To maximize
     * cross-language compatibility and performance, implementations are
     * recommended to prefer signed integer types over unsigned integer types
     * and to avoid uint64 indices unless they are required by an application.
     */
    indexType(obj) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? (obj || new Int()).__init(this.bb.__indirect(this.bb_pos + offset), this.bb) : null;
    }
    /**
     * By default, dictionaries are not ordered, or the order does not have
     * semantic meaning. In some statistical, applications, dictionary-encoding
     * is used to represent ordered categorical data, and we provide a way to
     * preserve that metadata here
     */
    isOrdered() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? !!this.bb.readInt8(this.bb_pos + offset) : false;
    }
    dictionaryKind() {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : DictionaryKind.DenseArray;
    }
    static startDictionaryEncoding(builder) {
      builder.startObject(4);
    }
    static addId(builder, id) {
      builder.addFieldInt64(0, id, builder.createLong(0, 0));
    }
    static addIndexType(builder, indexTypeOffset) {
      builder.addFieldOffset(1, indexTypeOffset, 0);
    }
    static addIsOrdered(builder, isOrdered) {
      builder.addFieldInt8(2, +isOrdered, 0);
    }
    static addDictionaryKind(builder, dictionaryKind) {
      builder.addFieldInt16(3, dictionaryKind, DictionaryKind.DenseArray);
    }
    static endDictionaryEncoding(builder) {
      const offset = builder.endObject();
      return offset;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/binary.mjs
  var Binary2 = class _Binary {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsBinary(bb, obj) {
      return (obj || new _Binary()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsBinary(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Binary()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static startBinary(builder) {
      builder.startObject(0);
    }
    static endBinary(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createBinary(builder) {
      _Binary.startBinary(builder);
      return _Binary.endBinary(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/bool.mjs
  var Bool2 = class _Bool {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsBool(bb, obj) {
      return (obj || new _Bool()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsBool(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Bool()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static startBool(builder) {
      builder.startObject(0);
    }
    static endBool(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createBool(builder) {
      _Bool.startBool(builder);
      return _Bool.endBool(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/date-unit.mjs
  var DateUnit2;
  (function(DateUnit3) {
    DateUnit3[DateUnit3["DAY"] = 0] = "DAY";
    DateUnit3[DateUnit3["MILLISECOND"] = 1] = "MILLISECOND";
  })(DateUnit2 || (DateUnit2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/date.mjs
  var Date2 = class _Date {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsDate(bb, obj) {
      return (obj || new _Date()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsDate(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Date()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    unit() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : DateUnit2.MILLISECOND;
    }
    static startDate(builder) {
      builder.startObject(1);
    }
    static addUnit(builder, unit) {
      builder.addFieldInt16(0, unit, DateUnit2.MILLISECOND);
    }
    static endDate(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createDate(builder, unit) {
      _Date.startDate(builder);
      _Date.addUnit(builder, unit);
      return _Date.endDate(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/decimal.mjs
  var Decimal2 = class _Decimal {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsDecimal(bb, obj) {
      return (obj || new _Decimal()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsDecimal(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Decimal()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * Total number of decimal digits
     */
    precision() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
    }
    /**
     * Number of digits after the decimal point "."
     */
    scale() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
    }
    /**
     * Number of bits per value. The only accepted widths are 128 and 256.
     * We use bitWidth for consistency with Int::bitWidth.
     */
    bitWidth() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 128;
    }
    static startDecimal(builder) {
      builder.startObject(3);
    }
    static addPrecision(builder, precision) {
      builder.addFieldInt32(0, precision, 0);
    }
    static addScale(builder, scale) {
      builder.addFieldInt32(1, scale, 0);
    }
    static addBitWidth(builder, bitWidth) {
      builder.addFieldInt32(2, bitWidth, 128);
    }
    static endDecimal(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createDecimal(builder, precision, scale, bitWidth) {
      _Decimal.startDecimal(builder);
      _Decimal.addPrecision(builder, precision);
      _Decimal.addScale(builder, scale);
      _Decimal.addBitWidth(builder, bitWidth);
      return _Decimal.endDecimal(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/time-unit.mjs
  var TimeUnit2;
  (function(TimeUnit3) {
    TimeUnit3[TimeUnit3["SECOND"] = 0] = "SECOND";
    TimeUnit3[TimeUnit3["MILLISECOND"] = 1] = "MILLISECOND";
    TimeUnit3[TimeUnit3["MICROSECOND"] = 2] = "MICROSECOND";
    TimeUnit3[TimeUnit3["NANOSECOND"] = 3] = "NANOSECOND";
  })(TimeUnit2 || (TimeUnit2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/fixed-size-binary.mjs
  var FixedSizeBinary2 = class _FixedSizeBinary {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsFixedSizeBinary(bb, obj) {
      return (obj || new _FixedSizeBinary()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsFixedSizeBinary(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _FixedSizeBinary()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * Number of bytes per value
     */
    byteWidth() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
    }
    static startFixedSizeBinary(builder) {
      builder.startObject(1);
    }
    static addByteWidth(builder, byteWidth) {
      builder.addFieldInt32(0, byteWidth, 0);
    }
    static endFixedSizeBinary(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createFixedSizeBinary(builder, byteWidth) {
      _FixedSizeBinary.startFixedSizeBinary(builder);
      _FixedSizeBinary.addByteWidth(builder, byteWidth);
      return _FixedSizeBinary.endFixedSizeBinary(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/fixed-size-list.mjs
  var FixedSizeList2 = class _FixedSizeList {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsFixedSizeList(bb, obj) {
      return (obj || new _FixedSizeList()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsFixedSizeList(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _FixedSizeList()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * Number of list items per value
     */
    listSize() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
    }
    static startFixedSizeList(builder) {
      builder.startObject(1);
    }
    static addListSize(builder, listSize) {
      builder.addFieldInt32(0, listSize, 0);
    }
    static endFixedSizeList(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createFixedSizeList(builder, listSize) {
      _FixedSizeList.startFixedSizeList(builder);
      _FixedSizeList.addListSize(builder, listSize);
      return _FixedSizeList.endFixedSizeList(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/precision.mjs
  var Precision2;
  (function(Precision3) {
    Precision3[Precision3["HALF"] = 0] = "HALF";
    Precision3[Precision3["SINGLE"] = 1] = "SINGLE";
    Precision3[Precision3["DOUBLE"] = 2] = "DOUBLE";
  })(Precision2 || (Precision2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/floating-point.mjs
  var FloatingPoint = class _FloatingPoint {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsFloatingPoint(bb, obj) {
      return (obj || new _FloatingPoint()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsFloatingPoint(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _FloatingPoint()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    precision() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : Precision2.HALF;
    }
    static startFloatingPoint(builder) {
      builder.startObject(1);
    }
    static addPrecision(builder, precision) {
      builder.addFieldInt16(0, precision, Precision2.HALF);
    }
    static endFloatingPoint(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createFloatingPoint(builder, precision) {
      _FloatingPoint.startFloatingPoint(builder);
      _FloatingPoint.addPrecision(builder, precision);
      return _FloatingPoint.endFloatingPoint(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/interval-unit.mjs
  var IntervalUnit2;
  (function(IntervalUnit3) {
    IntervalUnit3[IntervalUnit3["YEAR_MONTH"] = 0] = "YEAR_MONTH";
    IntervalUnit3[IntervalUnit3["DAY_TIME"] = 1] = "DAY_TIME";
    IntervalUnit3[IntervalUnit3["MONTH_DAY_NANO"] = 2] = "MONTH_DAY_NANO";
  })(IntervalUnit2 || (IntervalUnit2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/interval.mjs
  var Interval = class _Interval {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsInterval(bb, obj) {
      return (obj || new _Interval()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsInterval(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Interval()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    unit() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : IntervalUnit2.YEAR_MONTH;
    }
    static startInterval(builder) {
      builder.startObject(1);
    }
    static addUnit(builder, unit) {
      builder.addFieldInt16(0, unit, IntervalUnit2.YEAR_MONTH);
    }
    static endInterval(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createInterval(builder, unit) {
      _Interval.startInterval(builder);
      _Interval.addUnit(builder, unit);
      return _Interval.endInterval(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/list.mjs
  var List2 = class _List {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsList(bb, obj) {
      return (obj || new _List()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsList(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _List()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static startList(builder) {
      builder.startObject(0);
    }
    static endList(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createList(builder) {
      _List.startList(builder);
      return _List.endList(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/map.mjs
  var Map2 = class _Map {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsMap(bb, obj) {
      return (obj || new _Map()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsMap(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Map()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * Set to true if the keys within each value are sorted
     */
    keysSorted() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? !!this.bb.readInt8(this.bb_pos + offset) : false;
    }
    static startMap(builder) {
      builder.startObject(1);
    }
    static addKeysSorted(builder, keysSorted) {
      builder.addFieldInt8(0, +keysSorted, 0);
    }
    static endMap(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createMap(builder, keysSorted) {
      _Map.startMap(builder);
      _Map.addKeysSorted(builder, keysSorted);
      return _Map.endMap(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/null.mjs
  var Null2 = class _Null {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsNull(bb, obj) {
      return (obj || new _Null()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsNull(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Null()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static startNull(builder) {
      builder.startObject(0);
    }
    static endNull(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createNull(builder) {
      _Null.startNull(builder);
      return _Null.endNull(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/struct_.mjs
  var Struct_ = class _Struct_ {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsStruct_(bb, obj) {
      return (obj || new _Struct_()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsStruct_(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Struct_()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static startStruct_(builder) {
      builder.startObject(0);
    }
    static endStruct_(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createStruct_(builder) {
      _Struct_.startStruct_(builder);
      return _Struct_.endStruct_(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/time.mjs
  var Time = class _Time {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsTime(bb, obj) {
      return (obj || new _Time()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsTime(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Time()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    unit() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : TimeUnit2.MILLISECOND;
    }
    bitWidth() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.readInt32(this.bb_pos + offset) : 32;
    }
    static startTime(builder) {
      builder.startObject(2);
    }
    static addUnit(builder, unit) {
      builder.addFieldInt16(0, unit, TimeUnit2.MILLISECOND);
    }
    static addBitWidth(builder, bitWidth) {
      builder.addFieldInt32(1, bitWidth, 32);
    }
    static endTime(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createTime(builder, unit, bitWidth) {
      _Time.startTime(builder);
      _Time.addUnit(builder, unit);
      _Time.addBitWidth(builder, bitWidth);
      return _Time.endTime(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/timestamp.mjs
  var Timestamp = class _Timestamp {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsTimestamp(bb, obj) {
      return (obj || new _Timestamp()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsTimestamp(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Timestamp()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    unit() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : TimeUnit2.SECOND;
    }
    timezone(optionalEncoding) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.__string(this.bb_pos + offset, optionalEncoding) : null;
    }
    static startTimestamp(builder) {
      builder.startObject(2);
    }
    static addUnit(builder, unit) {
      builder.addFieldInt16(0, unit, TimeUnit2.SECOND);
    }
    static addTimezone(builder, timezoneOffset) {
      builder.addFieldOffset(1, timezoneOffset, 0);
    }
    static endTimestamp(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createTimestamp(builder, unit, timezoneOffset) {
      _Timestamp.startTimestamp(builder);
      _Timestamp.addUnit(builder, unit);
      _Timestamp.addTimezone(builder, timezoneOffset);
      return _Timestamp.endTimestamp(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/union-mode.mjs
  var UnionMode2;
  (function(UnionMode3) {
    UnionMode3[UnionMode3["Sparse"] = 0] = "Sparse";
    UnionMode3[UnionMode3["Dense"] = 1] = "Dense";
  })(UnionMode2 || (UnionMode2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/union.mjs
  var Union = class _Union {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsUnion(bb, obj) {
      return (obj || new _Union()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsUnion(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Union()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    mode() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : UnionMode2.Sparse;
    }
    typeIds(index) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.readInt32(this.bb.__vector(this.bb_pos + offset) + index * 4) : 0;
    }
    typeIdsLength() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    typeIdsArray() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? new Int32Array(this.bb.bytes().buffer, this.bb.bytes().byteOffset + this.bb.__vector(this.bb_pos + offset), this.bb.__vector_len(this.bb_pos + offset)) : null;
    }
    static startUnion(builder) {
      builder.startObject(2);
    }
    static addMode(builder, mode) {
      builder.addFieldInt16(0, mode, UnionMode2.Sparse);
    }
    static addTypeIds(builder, typeIdsOffset) {
      builder.addFieldOffset(1, typeIdsOffset, 0);
    }
    static createTypeIdsVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addInt32(data[i]);
      }
      return builder.endVector();
    }
    static startTypeIdsVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static endUnion(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createUnion(builder, mode, typeIdsOffset) {
      _Union.startUnion(builder);
      _Union.addMode(builder, mode);
      _Union.addTypeIds(builder, typeIdsOffset);
      return _Union.endUnion(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/utf8.mjs
  var Utf82 = class _Utf8 {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsUtf8(bb, obj) {
      return (obj || new _Utf8()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsUtf8(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Utf8()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static startUtf8(builder) {
      builder.startObject(0);
    }
    static endUtf8(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createUtf8(builder) {
      _Utf8.startUtf8(builder);
      return _Utf8.endUtf8(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/type.mjs
  var Type2;
  (function(Type3) {
    Type3[Type3["NONE"] = 0] = "NONE";
    Type3[Type3["Null"] = 1] = "Null";
    Type3[Type3["Int"] = 2] = "Int";
    Type3[Type3["FloatingPoint"] = 3] = "FloatingPoint";
    Type3[Type3["Binary"] = 4] = "Binary";
    Type3[Type3["Utf8"] = 5] = "Utf8";
    Type3[Type3["Bool"] = 6] = "Bool";
    Type3[Type3["Decimal"] = 7] = "Decimal";
    Type3[Type3["Date"] = 8] = "Date";
    Type3[Type3["Time"] = 9] = "Time";
    Type3[Type3["Timestamp"] = 10] = "Timestamp";
    Type3[Type3["Interval"] = 11] = "Interval";
    Type3[Type3["List"] = 12] = "List";
    Type3[Type3["Struct_"] = 13] = "Struct_";
    Type3[Type3["Union"] = 14] = "Union";
    Type3[Type3["FixedSizeBinary"] = 15] = "FixedSizeBinary";
    Type3[Type3["FixedSizeList"] = 16] = "FixedSizeList";
    Type3[Type3["Map"] = 17] = "Map";
    Type3[Type3["Duration"] = 18] = "Duration";
    Type3[Type3["LargeBinary"] = 19] = "LargeBinary";
    Type3[Type3["LargeUtf8"] = 20] = "LargeUtf8";
    Type3[Type3["LargeList"] = 21] = "LargeList";
  })(Type2 || (Type2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/field.mjs
  var Field = class _Field {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsField(bb, obj) {
      return (obj || new _Field()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsField(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Field()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    name(optionalEncoding) {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.__string(this.bb_pos + offset, optionalEncoding) : null;
    }
    /**
     * Whether or not this field can contain nulls. Should be true in general.
     */
    nullable() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? !!this.bb.readInt8(this.bb_pos + offset) : false;
    }
    typeType() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? this.bb.readUint8(this.bb_pos + offset) : Type2.NONE;
    }
    /**
     * This is the type of the decoded value if the field is dictionary encoded.
     */
    // @ts-ignore
    type(obj) {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? this.bb.__union(obj, this.bb_pos + offset) : null;
    }
    /**
     * Present only if the field is dictionary encoded.
     */
    dictionary(obj) {
      const offset = this.bb.__offset(this.bb_pos, 12);
      return offset ? (obj || new DictionaryEncoding()).__init(this.bb.__indirect(this.bb_pos + offset), this.bb) : null;
    }
    /**
     * children apply only to nested data types like Struct, List and Union. For
     * primitive types children will have length 0.
     */
    children(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 14);
      return offset ? (obj || new _Field()).__init(this.bb.__indirect(this.bb.__vector(this.bb_pos + offset) + index * 4), this.bb) : null;
    }
    childrenLength() {
      const offset = this.bb.__offset(this.bb_pos, 14);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    /**
     * User-defined metadata
     */
    customMetadata(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 16);
      return offset ? (obj || new KeyValue()).__init(this.bb.__indirect(this.bb.__vector(this.bb_pos + offset) + index * 4), this.bb) : null;
    }
    customMetadataLength() {
      const offset = this.bb.__offset(this.bb_pos, 16);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    static startField(builder) {
      builder.startObject(7);
    }
    static addName(builder, nameOffset) {
      builder.addFieldOffset(0, nameOffset, 0);
    }
    static addNullable(builder, nullable) {
      builder.addFieldInt8(1, +nullable, 0);
    }
    static addTypeType(builder, typeType) {
      builder.addFieldInt8(2, typeType, Type2.NONE);
    }
    static addType(builder, typeOffset) {
      builder.addFieldOffset(3, typeOffset, 0);
    }
    static addDictionary(builder, dictionaryOffset) {
      builder.addFieldOffset(4, dictionaryOffset, 0);
    }
    static addChildren(builder, childrenOffset) {
      builder.addFieldOffset(5, childrenOffset, 0);
    }
    static createChildrenVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addOffset(data[i]);
      }
      return builder.endVector();
    }
    static startChildrenVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static addCustomMetadata(builder, customMetadataOffset) {
      builder.addFieldOffset(6, customMetadataOffset, 0);
    }
    static createCustomMetadataVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addOffset(data[i]);
      }
      return builder.endVector();
    }
    static startCustomMetadataVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static endField(builder) {
      const offset = builder.endObject();
      return offset;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/schema.mjs
  var Schema = class _Schema {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsSchema(bb, obj) {
      return (obj || new _Schema()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsSchema(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Schema()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * endianness of the buffer
     * it is Little Endian by default
     * if endianness doesn't match the underlying system then the vectors need to be converted
     */
    endianness() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : Endianness.Little;
    }
    fields(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? (obj || new Field()).__init(this.bb.__indirect(this.bb.__vector(this.bb_pos + offset) + index * 4), this.bb) : null;
    }
    fieldsLength() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    customMetadata(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? (obj || new KeyValue()).__init(this.bb.__indirect(this.bb.__vector(this.bb_pos + offset) + index * 4), this.bb) : null;
    }
    customMetadataLength() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    /**
     * Features used in the stream/file.
     */
    features(index) {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? this.bb.readInt64(this.bb.__vector(this.bb_pos + offset) + index * 8) : this.bb.createLong(0, 0);
    }
    featuresLength() {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    static startSchema(builder) {
      builder.startObject(4);
    }
    static addEndianness(builder, endianness) {
      builder.addFieldInt16(0, endianness, Endianness.Little);
    }
    static addFields(builder, fieldsOffset) {
      builder.addFieldOffset(1, fieldsOffset, 0);
    }
    static createFieldsVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addOffset(data[i]);
      }
      return builder.endVector();
    }
    static startFieldsVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static addCustomMetadata(builder, customMetadataOffset) {
      builder.addFieldOffset(2, customMetadataOffset, 0);
    }
    static createCustomMetadataVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addOffset(data[i]);
      }
      return builder.endVector();
    }
    static startCustomMetadataVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static addFeatures(builder, featuresOffset) {
      builder.addFieldOffset(3, featuresOffset, 0);
    }
    static createFeaturesVector(builder, data) {
      builder.startVector(8, data.length, 8);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addInt64(data[i]);
      }
      return builder.endVector();
    }
    static startFeaturesVector(builder, numElems) {
      builder.startVector(8, numElems, 8);
    }
    static endSchema(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static finishSchemaBuffer(builder, offset) {
      builder.finish(offset);
    }
    static finishSizePrefixedSchemaBuffer(builder, offset) {
      builder.finish(offset, void 0, true);
    }
    static createSchema(builder, endianness, fieldsOffset, customMetadataOffset, featuresOffset) {
      _Schema.startSchema(builder);
      _Schema.addEndianness(builder, endianness);
      _Schema.addFields(builder, fieldsOffset);
      _Schema.addCustomMetadata(builder, customMetadataOffset);
      _Schema.addFeatures(builder, featuresOffset);
      return _Schema.endSchema(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/footer.mjs
  var Footer = class _Footer {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsFooter(bb, obj) {
      return (obj || new _Footer()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsFooter(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Footer()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    version() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : MetadataVersion2.V1;
    }
    schema(obj) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? (obj || new Schema()).__init(this.bb.__indirect(this.bb_pos + offset), this.bb) : null;
    }
    dictionaries(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? (obj || new Block()).__init(this.bb.__vector(this.bb_pos + offset) + index * 24, this.bb) : null;
    }
    dictionariesLength() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    recordBatches(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? (obj || new Block()).__init(this.bb.__vector(this.bb_pos + offset) + index * 24, this.bb) : null;
    }
    recordBatchesLength() {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    /**
     * User-defined metadata
     */
    customMetadata(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 12);
      return offset ? (obj || new KeyValue()).__init(this.bb.__indirect(this.bb.__vector(this.bb_pos + offset) + index * 4), this.bb) : null;
    }
    customMetadataLength() {
      const offset = this.bb.__offset(this.bb_pos, 12);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    static startFooter(builder) {
      builder.startObject(5);
    }
    static addVersion(builder, version) {
      builder.addFieldInt16(0, version, MetadataVersion2.V1);
    }
    static addSchema(builder, schemaOffset) {
      builder.addFieldOffset(1, schemaOffset, 0);
    }
    static addDictionaries(builder, dictionariesOffset) {
      builder.addFieldOffset(2, dictionariesOffset, 0);
    }
    static startDictionariesVector(builder, numElems) {
      builder.startVector(24, numElems, 8);
    }
    static addRecordBatches(builder, recordBatchesOffset) {
      builder.addFieldOffset(3, recordBatchesOffset, 0);
    }
    static startRecordBatchesVector(builder, numElems) {
      builder.startVector(24, numElems, 8);
    }
    static addCustomMetadata(builder, customMetadataOffset) {
      builder.addFieldOffset(4, customMetadataOffset, 0);
    }
    static createCustomMetadataVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addOffset(data[i]);
      }
      return builder.endVector();
    }
    static startCustomMetadataVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static endFooter(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static finishFooterBuffer(builder, offset) {
      builder.finish(offset);
    }
    static finishSizePrefixedFooterBuffer(builder, offset) {
      builder.finish(offset, void 0, true);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/schema.mjs
  var Schema2 = class _Schema {
    constructor(fields = [], metadata, dictionaries) {
      this.fields = fields || [];
      this.metadata = metadata || /* @__PURE__ */ new Map();
      if (!dictionaries) {
        dictionaries = generateDictionaryMap(fields);
      }
      this.dictionaries = dictionaries;
    }
    get [Symbol.toStringTag]() {
      return "Schema";
    }
    get names() {
      return this.fields.map((f) => f.name);
    }
    toString() {
      return `Schema<{ ${this.fields.map((f, i) => `${i}: ${f}`).join(", ")} }>`;
    }
    /**
     * Construct a new Schema containing only specified fields.
     *
     * @param fieldNames Names of fields to keep.
     * @returns A new Schema of fields matching the specified names.
     */
    select(fieldNames) {
      const names = new Set(fieldNames);
      const fields = this.fields.filter((f) => names.has(f.name));
      return new _Schema(fields, this.metadata);
    }
    /**
     * Construct a new Schema containing only fields at the specified indices.
     *
     * @param fieldIndices Indices of fields to keep.
     * @returns A new Schema of fields at the specified indices.
     */
    selectAt(fieldIndices) {
      const fields = fieldIndices.map((i) => this.fields[i]).filter(Boolean);
      return new _Schema(fields, this.metadata);
    }
    assign(...args) {
      const other = args[0] instanceof _Schema ? args[0] : Array.isArray(args[0]) ? new _Schema(args[0]) : new _Schema(args);
      const curFields = [...this.fields];
      const metadata = mergeMaps(mergeMaps(/* @__PURE__ */ new Map(), this.metadata), other.metadata);
      const newFields = other.fields.filter((f2) => {
        const i = curFields.findIndex((f) => f.name === f2.name);
        return ~i ? (curFields[i] = f2.clone({
          metadata: mergeMaps(mergeMaps(/* @__PURE__ */ new Map(), curFields[i].metadata), f2.metadata)
        })) && false : true;
      });
      const newDictionaries = generateDictionaryMap(newFields, /* @__PURE__ */ new Map());
      return new _Schema([...curFields, ...newFields], metadata, new Map([...this.dictionaries, ...newDictionaries]));
    }
  };
  Schema2.prototype.fields = null;
  Schema2.prototype.metadata = null;
  Schema2.prototype.dictionaries = null;
  var Field2 = class _Field {
    constructor(name, type2, nullable = false, metadata) {
      this.name = name;
      this.type = type2;
      this.nullable = nullable;
      this.metadata = metadata || /* @__PURE__ */ new Map();
    }
    /** @nocollapse */
    static new(...args) {
      let [name, type2, nullable, metadata] = args;
      if (args[0] && typeof args[0] === "object") {
        ({ name } = args[0]);
        type2 === void 0 && (type2 = args[0].type);
        nullable === void 0 && (nullable = args[0].nullable);
        metadata === void 0 && (metadata = args[0].metadata);
      }
      return new _Field(`${name}`, type2, nullable, metadata);
    }
    get typeId() {
      return this.type.typeId;
    }
    get [Symbol.toStringTag]() {
      return "Field";
    }
    toString() {
      return `${this.name}: ${this.type}`;
    }
    clone(...args) {
      let [name, type2, nullable, metadata] = args;
      !args[0] || typeof args[0] !== "object" ? [name = this.name, type2 = this.type, nullable = this.nullable, metadata = this.metadata] = args : { name = this.name, type: type2 = this.type, nullable = this.nullable, metadata = this.metadata } = args[0];
      return _Field.new(name, type2, nullable, metadata);
    }
  };
  Field2.prototype.type = null;
  Field2.prototype.name = null;
  Field2.prototype.nullable = null;
  Field2.prototype.metadata = null;
  function mergeMaps(m1, m2) {
    return new Map([...m1 || /* @__PURE__ */ new Map(), ...m2 || /* @__PURE__ */ new Map()]);
  }
  function generateDictionaryMap(fields, dictionaries = /* @__PURE__ */ new Map()) {
    for (let i = -1, n = fields.length; ++i < n; ) {
      const field = fields[i];
      const type2 = field.type;
      if (DataType.isDictionary(type2)) {
        if (!dictionaries.has(type2.id)) {
          dictionaries.set(type2.id, type2.dictionary);
        } else if (dictionaries.get(type2.id) !== type2.dictionary) {
          throw new Error(`Cannot create Schema containing two different dictionaries with the same Id`);
        }
      }
      if (type2.children && type2.children.length > 0) {
        generateDictionaryMap(type2.children, dictionaries);
      }
    }
    return dictionaries;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/metadata/file.mjs
  var Long2 = Long;
  var Builder3 = Builder2;
  var ByteBuffer2 = ByteBuffer;
  var Footer_ = class {
    constructor(schema, version = MetadataVersion.V4, recordBatches, dictionaryBatches) {
      this.schema = schema;
      this.version = version;
      recordBatches && (this._recordBatches = recordBatches);
      dictionaryBatches && (this._dictionaryBatches = dictionaryBatches);
    }
    /** @nocollapse */
    static decode(buf) {
      buf = new ByteBuffer2(toUint8Array(buf));
      const footer = Footer.getRootAsFooter(buf);
      const schema = Schema2.decode(footer.schema());
      return new OffHeapFooter(schema, footer);
    }
    /** @nocollapse */
    static encode(footer) {
      const b = new Builder3();
      const schemaOffset = Schema2.encode(b, footer.schema);
      Footer.startRecordBatchesVector(b, footer.numRecordBatches);
      for (const rb of [...footer.recordBatches()].slice().reverse()) {
        FileBlock.encode(b, rb);
      }
      const recordBatchesOffset = b.endVector();
      Footer.startDictionariesVector(b, footer.numDictionaries);
      for (const db of [...footer.dictionaryBatches()].slice().reverse()) {
        FileBlock.encode(b, db);
      }
      const dictionaryBatchesOffset = b.endVector();
      Footer.startFooter(b);
      Footer.addSchema(b, schemaOffset);
      Footer.addVersion(b, MetadataVersion.V4);
      Footer.addRecordBatches(b, recordBatchesOffset);
      Footer.addDictionaries(b, dictionaryBatchesOffset);
      Footer.finishFooterBuffer(b, Footer.endFooter(b));
      return b.asUint8Array();
    }
    get numRecordBatches() {
      return this._recordBatches.length;
    }
    get numDictionaries() {
      return this._dictionaryBatches.length;
    }
    *recordBatches() {
      for (let block, i = -1, n = this.numRecordBatches; ++i < n; ) {
        if (block = this.getRecordBatch(i)) {
          yield block;
        }
      }
    }
    *dictionaryBatches() {
      for (let block, i = -1, n = this.numDictionaries; ++i < n; ) {
        if (block = this.getDictionaryBatch(i)) {
          yield block;
        }
      }
    }
    getRecordBatch(index) {
      return index >= 0 && index < this.numRecordBatches && this._recordBatches[index] || null;
    }
    getDictionaryBatch(index) {
      return index >= 0 && index < this.numDictionaries && this._dictionaryBatches[index] || null;
    }
  };
  var OffHeapFooter = class extends Footer_ {
    constructor(schema, _footer) {
      super(schema, _footer.version());
      this._footer = _footer;
    }
    get numRecordBatches() {
      return this._footer.recordBatchesLength();
    }
    get numDictionaries() {
      return this._footer.dictionariesLength();
    }
    getRecordBatch(index) {
      if (index >= 0 && index < this.numRecordBatches) {
        const fileBlock = this._footer.recordBatches(index);
        if (fileBlock) {
          return FileBlock.decode(fileBlock);
        }
      }
      return null;
    }
    getDictionaryBatch(index) {
      if (index >= 0 && index < this.numDictionaries) {
        const fileBlock = this._footer.dictionaries(index);
        if (fileBlock) {
          return FileBlock.decode(fileBlock);
        }
      }
      return null;
    }
  };
  var FileBlock = class _FileBlock {
    constructor(metaDataLength, bodyLength, offset) {
      this.metaDataLength = metaDataLength;
      this.offset = typeof offset === "number" ? offset : offset.low;
      this.bodyLength = typeof bodyLength === "number" ? bodyLength : bodyLength.low;
    }
    /** @nocollapse */
    static decode(block) {
      return new _FileBlock(block.metaDataLength(), block.bodyLength(), block.offset());
    }
    /** @nocollapse */
    static encode(b, fileBlock) {
      const { metaDataLength } = fileBlock;
      const offset = new Long2(fileBlock.offset, 0);
      const bodyLength = new Long2(fileBlock.bodyLength, 0);
      return Block.createBlock(b, offset, metaDataLength, bodyLength);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/interfaces.mjs
  var ITERATOR_DONE = Object.freeze({ done: true, value: void 0 });
  var ArrowJSON = class {
    constructor(_json) {
      this._json = _json;
    }
    get schema() {
      return this._json["schema"];
    }
    get batches() {
      return this._json["batches"] || [];
    }
    get dictionaries() {
      return this._json["dictionaries"] || [];
    }
  };
  var ReadableInterop = class {
    tee() {
      return this._getDOMStream().tee();
    }
    pipe(writable, options) {
      return this._getNodeStream().pipe(writable, options);
    }
    pipeTo(writable, options) {
      return this._getDOMStream().pipeTo(writable, options);
    }
    pipeThrough(duplex, options) {
      return this._getDOMStream().pipeThrough(duplex, options);
    }
    _getDOMStream() {
      return this._DOMStream || (this._DOMStream = this.toDOMStream());
    }
    _getNodeStream() {
      return this._nodeStream || (this._nodeStream = this.toNodeStream());
    }
  };
  var AsyncQueue = class extends ReadableInterop {
    constructor() {
      super();
      this._values = [];
      this.resolvers = [];
      this._closedPromise = new Promise((r) => this._closedPromiseResolve = r);
    }
    get closed() {
      return this._closedPromise;
    }
    cancel(reason) {
      return __awaiter(this, void 0, void 0, function* () {
        yield this.return(reason);
      });
    }
    write(value) {
      if (this._ensureOpen()) {
        this.resolvers.length <= 0 ? this._values.push(value) : this.resolvers.shift().resolve({ done: false, value });
      }
    }
    abort(value) {
      if (this._closedPromiseResolve) {
        this.resolvers.length <= 0 ? this._error = { error: value } : this.resolvers.shift().reject({ done: true, value });
      }
    }
    close() {
      if (this._closedPromiseResolve) {
        const { resolvers } = this;
        while (resolvers.length > 0) {
          resolvers.shift().resolve(ITERATOR_DONE);
        }
        this._closedPromiseResolve();
        this._closedPromiseResolve = void 0;
      }
    }
    [Symbol.asyncIterator]() {
      return this;
    }
    toDOMStream(options) {
      return adapters_default.toDOMStream(this._closedPromiseResolve || this._error ? this : this._values, options);
    }
    toNodeStream(options) {
      return adapters_default.toNodeStream(this._closedPromiseResolve || this._error ? this : this._values, options);
    }
    throw(_) {
      return __awaiter(this, void 0, void 0, function* () {
        yield this.abort(_);
        return ITERATOR_DONE;
      });
    }
    return(_) {
      return __awaiter(this, void 0, void 0, function* () {
        yield this.close();
        return ITERATOR_DONE;
      });
    }
    read(size) {
      return __awaiter(this, void 0, void 0, function* () {
        return (yield this.next(size, "read")).value;
      });
    }
    peek(size) {
      return __awaiter(this, void 0, void 0, function* () {
        return (yield this.next(size, "peek")).value;
      });
    }
    next(..._args) {
      if (this._values.length > 0) {
        return Promise.resolve({ done: false, value: this._values.shift() });
      } else if (this._error) {
        return Promise.reject({ done: true, value: this._error.error });
      } else if (!this._closedPromiseResolve) {
        return Promise.resolve(ITERATOR_DONE);
      } else {
        return new Promise((resolve, reject) => {
          this.resolvers.push({ resolve, reject });
        });
      }
    }
    _ensureOpen() {
      if (this._closedPromiseResolve) {
        return true;
      }
      throw new Error(`AsyncQueue is closed`);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/stream.mjs
  var AsyncByteQueue = class extends AsyncQueue {
    write(value) {
      if ((value = toUint8Array(value)).byteLength > 0) {
        return super.write(value);
      }
    }
    toString(sync = false) {
      return sync ? decodeUtf8(this.toUint8Array(true)) : this.toUint8Array(false).then(decodeUtf8);
    }
    toUint8Array(sync = false) {
      return sync ? joinUint8Arrays(this._values)[0] : (() => __awaiter(this, void 0, void 0, function* () {
        var e_1, _a5;
        const buffers = [];
        let byteLength = 0;
        try {
          for (var _b2 = __asyncValues(this), _c2; _c2 = yield _b2.next(), !_c2.done; ) {
            const chunk = _c2.value;
            buffers.push(chunk);
            byteLength += chunk.byteLength;
          }
        } catch (e_1_1) {
          e_1 = { error: e_1_1 };
        } finally {
          try {
            if (_c2 && !_c2.done && (_a5 = _b2.return)) yield _a5.call(_b2);
          } finally {
            if (e_1) throw e_1.error;
          }
        }
        return joinUint8Arrays(buffers, byteLength)[0];
      }))();
    }
  };
  var ByteStream = class {
    constructor(source) {
      if (source) {
        this.source = new ByteStreamSource(adapters_default.fromIterable(source));
      }
    }
    [Symbol.iterator]() {
      return this;
    }
    next(value) {
      return this.source.next(value);
    }
    throw(value) {
      return this.source.throw(value);
    }
    return(value) {
      return this.source.return(value);
    }
    peek(size) {
      return this.source.peek(size);
    }
    read(size) {
      return this.source.read(size);
    }
  };
  var AsyncByteStream = class _AsyncByteStream {
    constructor(source) {
      if (source instanceof _AsyncByteStream) {
        this.source = source.source;
      } else if (source instanceof AsyncByteQueue) {
        this.source = new AsyncByteStreamSource(adapters_default.fromAsyncIterable(source));
      } else if (isReadableNodeStream(source)) {
        this.source = new AsyncByteStreamSource(adapters_default.fromNodeStream(source));
      } else if (isReadableDOMStream(source)) {
        this.source = new AsyncByteStreamSource(adapters_default.fromDOMStream(source));
      } else if (isFetchResponse(source)) {
        this.source = new AsyncByteStreamSource(adapters_default.fromDOMStream(source.body));
      } else if (isIterable(source)) {
        this.source = new AsyncByteStreamSource(adapters_default.fromIterable(source));
      } else if (isPromise(source)) {
        this.source = new AsyncByteStreamSource(adapters_default.fromAsyncIterable(source));
      } else if (isAsyncIterable(source)) {
        this.source = new AsyncByteStreamSource(adapters_default.fromAsyncIterable(source));
      }
    }
    [Symbol.asyncIterator]() {
      return this;
    }
    next(value) {
      return this.source.next(value);
    }
    throw(value) {
      return this.source.throw(value);
    }
    return(value) {
      return this.source.return(value);
    }
    get closed() {
      return this.source.closed;
    }
    cancel(reason) {
      return this.source.cancel(reason);
    }
    peek(size) {
      return this.source.peek(size);
    }
    read(size) {
      return this.source.read(size);
    }
  };
  var ByteStreamSource = class {
    constructor(source) {
      this.source = source;
    }
    cancel(reason) {
      this.return(reason);
    }
    peek(size) {
      return this.next(size, "peek").value;
    }
    read(size) {
      return this.next(size, "read").value;
    }
    next(size, cmd = "read") {
      return this.source.next({ cmd, size });
    }
    throw(value) {
      return Object.create(this.source.throw && this.source.throw(value) || ITERATOR_DONE);
    }
    return(value) {
      return Object.create(this.source.return && this.source.return(value) || ITERATOR_DONE);
    }
  };
  var AsyncByteStreamSource = class {
    constructor(source) {
      this.source = source;
      this._closedPromise = new Promise((r) => this._closedPromiseResolve = r);
    }
    cancel(reason) {
      return __awaiter(this, void 0, void 0, function* () {
        yield this.return(reason);
      });
    }
    get closed() {
      return this._closedPromise;
    }
    read(size) {
      return __awaiter(this, void 0, void 0, function* () {
        return (yield this.next(size, "read")).value;
      });
    }
    peek(size) {
      return __awaiter(this, void 0, void 0, function* () {
        return (yield this.next(size, "peek")).value;
      });
    }
    next(size, cmd = "read") {
      return __awaiter(this, void 0, void 0, function* () {
        return yield this.source.next({ cmd, size });
      });
    }
    throw(value) {
      return __awaiter(this, void 0, void 0, function* () {
        const result = this.source.throw && (yield this.source.throw(value)) || ITERATOR_DONE;
        this._closedPromiseResolve && this._closedPromiseResolve();
        this._closedPromiseResolve = void 0;
        return Object.create(result);
      });
    }
    return(value) {
      return __awaiter(this, void 0, void 0, function* () {
        const result = this.source.return && (yield this.source.return(value)) || ITERATOR_DONE;
        this._closedPromiseResolve && this._closedPromiseResolve();
        this._closedPromiseResolve = void 0;
        return Object.create(result);
      });
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/file.mjs
  var RandomAccessFile = class extends ByteStream {
    constructor(buffer, byteLength) {
      super();
      this.position = 0;
      this.buffer = toUint8Array(buffer);
      this.size = typeof byteLength === "undefined" ? this.buffer.byteLength : byteLength;
    }
    readInt32(position) {
      const { buffer, byteOffset } = this.readAt(position, 4);
      return new DataView(buffer, byteOffset).getInt32(0, true);
    }
    seek(position) {
      this.position = Math.min(position, this.size);
      return position < this.size;
    }
    read(nBytes) {
      const { buffer, size, position } = this;
      if (buffer && position < size) {
        if (typeof nBytes !== "number") {
          nBytes = Number.POSITIVE_INFINITY;
        }
        this.position = Math.min(size, position + Math.min(size - position, nBytes));
        return buffer.subarray(position, this.position);
      }
      return null;
    }
    readAt(position, nBytes) {
      const buf = this.buffer;
      const end = Math.min(this.size, position + nBytes);
      return buf ? buf.subarray(position, end) : new Uint8Array(nBytes);
    }
    close() {
      this.buffer && (this.buffer = null);
    }
    throw(value) {
      this.close();
      return { done: true, value };
    }
    return(value) {
      this.close();
      return { done: true, value };
    }
  };
  var AsyncRandomAccessFile = class extends AsyncByteStream {
    constructor(file, byteLength) {
      super();
      this.position = 0;
      this._handle = file;
      if (typeof byteLength === "number") {
        this.size = byteLength;
      } else {
        this._pending = (() => __awaiter(this, void 0, void 0, function* () {
          this.size = (yield file.stat()).size;
          delete this._pending;
        }))();
      }
    }
    readInt32(position) {
      return __awaiter(this, void 0, void 0, function* () {
        const { buffer, byteOffset } = yield this.readAt(position, 4);
        return new DataView(buffer, byteOffset).getInt32(0, true);
      });
    }
    seek(position) {
      return __awaiter(this, void 0, void 0, function* () {
        this._pending && (yield this._pending);
        this.position = Math.min(position, this.size);
        return position < this.size;
      });
    }
    read(nBytes) {
      return __awaiter(this, void 0, void 0, function* () {
        this._pending && (yield this._pending);
        const { _handle: file, size, position } = this;
        if (file && position < size) {
          if (typeof nBytes !== "number") {
            nBytes = Number.POSITIVE_INFINITY;
          }
          let pos = position, offset = 0, bytesRead = 0;
          const end = Math.min(size, pos + Math.min(size - pos, nBytes));
          const buffer = new Uint8Array(Math.max(0, (this.position = end) - pos));
          while ((pos += bytesRead) < end && (offset += bytesRead) < buffer.byteLength) {
            ({ bytesRead } = yield file.read(buffer, offset, buffer.byteLength - offset, pos));
          }
          return buffer;
        }
        return null;
      });
    }
    readAt(position, nBytes) {
      return __awaiter(this, void 0, void 0, function* () {
        this._pending && (yield this._pending);
        const { _handle: file, size } = this;
        if (file && position + nBytes < size) {
          const end = Math.min(size, position + nBytes);
          const buffer = new Uint8Array(end - position);
          return (yield file.read(buffer, 0, nBytes, position)).buffer;
        }
        return new Uint8Array(nBytes);
      });
    }
    close() {
      return __awaiter(this, void 0, void 0, function* () {
        const f = this._handle;
        this._handle = null;
        f && (yield f.close());
      });
    }
    throw(value) {
      return __awaiter(this, void 0, void 0, function* () {
        yield this.close();
        return { done: true, value };
      });
    }
    return(value) {
      return __awaiter(this, void 0, void 0, function* () {
        yield this.close();
        return { done: true, value };
      });
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/int.mjs
  var int_exports = {};
  __export(int_exports, {
    BaseInt64: () => BaseInt64,
    Int128: () => Int128,
    Int64: () => Int642,
    Uint64: () => Uint642
  });
  var carryBit16 = 1 << 16;
  function intAsHex(value) {
    if (value < 0) {
      value = 4294967295 + value + 1;
    }
    return `0x${value.toString(16)}`;
  }
  var kInt32DecimalDigits = 8;
  var kPowersOfTen = [
    1,
    10,
    100,
    1e3,
    1e4,
    1e5,
    1e6,
    1e7,
    1e8
  ];
  var BaseInt64 = class {
    constructor(buffer) {
      this.buffer = buffer;
    }
    high() {
      return this.buffer[1];
    }
    low() {
      return this.buffer[0];
    }
    _times(other) {
      const L3 = new Uint32Array([
        this.buffer[1] >>> 16,
        this.buffer[1] & 65535,
        this.buffer[0] >>> 16,
        this.buffer[0] & 65535
      ]);
      const R = new Uint32Array([
        other.buffer[1] >>> 16,
        other.buffer[1] & 65535,
        other.buffer[0] >>> 16,
        other.buffer[0] & 65535
      ]);
      let product = L3[3] * R[3];
      this.buffer[0] = product & 65535;
      let sum2 = product >>> 16;
      product = L3[2] * R[3];
      sum2 += product;
      product = L3[3] * R[2] >>> 0;
      sum2 += product;
      this.buffer[0] += sum2 << 16;
      this.buffer[1] = sum2 >>> 0 < product ? carryBit16 : 0;
      this.buffer[1] += sum2 >>> 16;
      this.buffer[1] += L3[1] * R[3] + L3[2] * R[2] + L3[3] * R[1];
      this.buffer[1] += L3[0] * R[3] + L3[1] * R[2] + L3[2] * R[1] + L3[3] * R[0] << 16;
      return this;
    }
    _plus(other) {
      const sum2 = this.buffer[0] + other.buffer[0] >>> 0;
      this.buffer[1] += other.buffer[1];
      if (sum2 < this.buffer[0] >>> 0) {
        ++this.buffer[1];
      }
      this.buffer[0] = sum2;
    }
    lessThan(other) {
      return this.buffer[1] < other.buffer[1] || this.buffer[1] === other.buffer[1] && this.buffer[0] < other.buffer[0];
    }
    equals(other) {
      return this.buffer[1] === other.buffer[1] && this.buffer[0] == other.buffer[0];
    }
    greaterThan(other) {
      return other.lessThan(this);
    }
    hex() {
      return `${intAsHex(this.buffer[1])} ${intAsHex(this.buffer[0])}`;
    }
  };
  var Uint642 = class _Uint64 extends BaseInt64 {
    times(other) {
      this._times(other);
      return this;
    }
    plus(other) {
      this._plus(other);
      return this;
    }
    /** @nocollapse */
    static from(val, out_buffer = new Uint32Array(2)) {
      return _Uint64.fromString(typeof val === "string" ? val : val.toString(), out_buffer);
    }
    /** @nocollapse */
    static fromNumber(num, out_buffer = new Uint32Array(2)) {
      return _Uint64.fromString(num.toString(), out_buffer);
    }
    /** @nocollapse */
    static fromString(str, out_buffer = new Uint32Array(2)) {
      const length = str.length;
      const out = new _Uint64(out_buffer);
      for (let posn = 0; posn < length; ) {
        const group = kInt32DecimalDigits < length - posn ? kInt32DecimalDigits : length - posn;
        const chunk = new _Uint64(new Uint32Array([Number.parseInt(str.slice(posn, posn + group), 10), 0]));
        const multiple = new _Uint64(new Uint32Array([kPowersOfTen[group], 0]));
        out.times(multiple);
        out.plus(chunk);
        posn += group;
      }
      return out;
    }
    /** @nocollapse */
    static convertArray(values) {
      const data = new Uint32Array(values.length * 2);
      for (let i = -1, n = values.length; ++i < n; ) {
        _Uint64.from(values[i], new Uint32Array(data.buffer, data.byteOffset + 2 * i * 4, 2));
      }
      return data;
    }
    /** @nocollapse */
    static multiply(left, right) {
      const rtrn = new _Uint64(new Uint32Array(left.buffer));
      return rtrn.times(right);
    }
    /** @nocollapse */
    static add(left, right) {
      const rtrn = new _Uint64(new Uint32Array(left.buffer));
      return rtrn.plus(right);
    }
  };
  var Int642 = class _Int64 extends BaseInt64 {
    negate() {
      this.buffer[0] = ~this.buffer[0] + 1;
      this.buffer[1] = ~this.buffer[1];
      if (this.buffer[0] == 0) {
        ++this.buffer[1];
      }
      return this;
    }
    times(other) {
      this._times(other);
      return this;
    }
    plus(other) {
      this._plus(other);
      return this;
    }
    lessThan(other) {
      const this_high = this.buffer[1] << 0;
      const other_high = other.buffer[1] << 0;
      return this_high < other_high || this_high === other_high && this.buffer[0] < other.buffer[0];
    }
    /** @nocollapse */
    static from(val, out_buffer = new Uint32Array(2)) {
      return _Int64.fromString(typeof val === "string" ? val : val.toString(), out_buffer);
    }
    /** @nocollapse */
    static fromNumber(num, out_buffer = new Uint32Array(2)) {
      return _Int64.fromString(num.toString(), out_buffer);
    }
    /** @nocollapse */
    static fromString(str, out_buffer = new Uint32Array(2)) {
      const negate = str.startsWith("-");
      const length = str.length;
      const out = new _Int64(out_buffer);
      for (let posn = negate ? 1 : 0; posn < length; ) {
        const group = kInt32DecimalDigits < length - posn ? kInt32DecimalDigits : length - posn;
        const chunk = new _Int64(new Uint32Array([Number.parseInt(str.slice(posn, posn + group), 10), 0]));
        const multiple = new _Int64(new Uint32Array([kPowersOfTen[group], 0]));
        out.times(multiple);
        out.plus(chunk);
        posn += group;
      }
      return negate ? out.negate() : out;
    }
    /** @nocollapse */
    static convertArray(values) {
      const data = new Uint32Array(values.length * 2);
      for (let i = -1, n = values.length; ++i < n; ) {
        _Int64.from(values[i], new Uint32Array(data.buffer, data.byteOffset + 2 * i * 4, 2));
      }
      return data;
    }
    /** @nocollapse */
    static multiply(left, right) {
      const rtrn = new _Int64(new Uint32Array(left.buffer));
      return rtrn.times(right);
    }
    /** @nocollapse */
    static add(left, right) {
      const rtrn = new _Int64(new Uint32Array(left.buffer));
      return rtrn.plus(right);
    }
  };
  var Int128 = class _Int128 {
    constructor(buffer) {
      this.buffer = buffer;
    }
    high() {
      return new Int642(new Uint32Array(this.buffer.buffer, this.buffer.byteOffset + 8, 2));
    }
    low() {
      return new Int642(new Uint32Array(this.buffer.buffer, this.buffer.byteOffset, 2));
    }
    negate() {
      this.buffer[0] = ~this.buffer[0] + 1;
      this.buffer[1] = ~this.buffer[1];
      this.buffer[2] = ~this.buffer[2];
      this.buffer[3] = ~this.buffer[3];
      if (this.buffer[0] == 0) {
        ++this.buffer[1];
      }
      if (this.buffer[1] == 0) {
        ++this.buffer[2];
      }
      if (this.buffer[2] == 0) {
        ++this.buffer[3];
      }
      return this;
    }
    times(other) {
      const L0 = new Uint642(new Uint32Array([this.buffer[3], 0]));
      const L1 = new Uint642(new Uint32Array([this.buffer[2], 0]));
      const L22 = new Uint642(new Uint32Array([this.buffer[1], 0]));
      const L3 = new Uint642(new Uint32Array([this.buffer[0], 0]));
      const R0 = new Uint642(new Uint32Array([other.buffer[3], 0]));
      const R1 = new Uint642(new Uint32Array([other.buffer[2], 0]));
      const R2 = new Uint642(new Uint32Array([other.buffer[1], 0]));
      const R3 = new Uint642(new Uint32Array([other.buffer[0], 0]));
      let product = Uint642.multiply(L3, R3);
      this.buffer[0] = product.low();
      const sum2 = new Uint642(new Uint32Array([product.high(), 0]));
      product = Uint642.multiply(L22, R3);
      sum2.plus(product);
      product = Uint642.multiply(L3, R2);
      sum2.plus(product);
      this.buffer[1] = sum2.low();
      this.buffer[3] = sum2.lessThan(product) ? 1 : 0;
      this.buffer[2] = sum2.high();
      const high = new Uint642(new Uint32Array(this.buffer.buffer, this.buffer.byteOffset + 8, 2));
      high.plus(Uint642.multiply(L1, R3)).plus(Uint642.multiply(L22, R2)).plus(Uint642.multiply(L3, R1));
      this.buffer[3] += Uint642.multiply(L0, R3).plus(Uint642.multiply(L1, R2)).plus(Uint642.multiply(L22, R1)).plus(Uint642.multiply(L3, R0)).low();
      return this;
    }
    plus(other) {
      const sums = new Uint32Array(4);
      sums[3] = this.buffer[3] + other.buffer[3] >>> 0;
      sums[2] = this.buffer[2] + other.buffer[2] >>> 0;
      sums[1] = this.buffer[1] + other.buffer[1] >>> 0;
      sums[0] = this.buffer[0] + other.buffer[0] >>> 0;
      if (sums[0] < this.buffer[0] >>> 0) {
        ++sums[1];
      }
      if (sums[1] < this.buffer[1] >>> 0) {
        ++sums[2];
      }
      if (sums[2] < this.buffer[2] >>> 0) {
        ++sums[3];
      }
      this.buffer[3] = sums[3];
      this.buffer[2] = sums[2];
      this.buffer[1] = sums[1];
      this.buffer[0] = sums[0];
      return this;
    }
    hex() {
      return `${intAsHex(this.buffer[3])} ${intAsHex(this.buffer[2])} ${intAsHex(this.buffer[1])} ${intAsHex(this.buffer[0])}`;
    }
    /** @nocollapse */
    static multiply(left, right) {
      const rtrn = new _Int128(new Uint32Array(left.buffer));
      return rtrn.times(right);
    }
    /** @nocollapse */
    static add(left, right) {
      const rtrn = new _Int128(new Uint32Array(left.buffer));
      return rtrn.plus(right);
    }
    /** @nocollapse */
    static from(val, out_buffer = new Uint32Array(4)) {
      return _Int128.fromString(typeof val === "string" ? val : val.toString(), out_buffer);
    }
    /** @nocollapse */
    static fromNumber(num, out_buffer = new Uint32Array(4)) {
      return _Int128.fromString(num.toString(), out_buffer);
    }
    /** @nocollapse */
    static fromString(str, out_buffer = new Uint32Array(4)) {
      const negate = str.startsWith("-");
      const length = str.length;
      const out = new _Int128(out_buffer);
      for (let posn = negate ? 1 : 0; posn < length; ) {
        const group = kInt32DecimalDigits < length - posn ? kInt32DecimalDigits : length - posn;
        const chunk = new _Int128(new Uint32Array([Number.parseInt(str.slice(posn, posn + group), 10), 0, 0, 0]));
        const multiple = new _Int128(new Uint32Array([kPowersOfTen[group], 0, 0, 0]));
        out.times(multiple);
        out.plus(chunk);
        posn += group;
      }
      return negate ? out.negate() : out;
    }
    /** @nocollapse */
    static convertArray(values) {
      const data = new Uint32Array(values.length * 4);
      for (let i = -1, n = values.length; ++i < n; ) {
        _Int128.from(values[i], new Uint32Array(data.buffer, data.byteOffset + 4 * 4 * i, 4));
      }
      return data;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/vectorloader.mjs
  var VectorLoader = class extends Visitor {
    constructor(bytes, nodes, buffers, dictionaries) {
      super();
      this.nodesIndex = -1;
      this.buffersIndex = -1;
      this.bytes = bytes;
      this.nodes = nodes;
      this.buffers = buffers;
      this.dictionaries = dictionaries;
    }
    visit(node) {
      return super.visit(node instanceof Field2 ? node.type : node);
    }
    visitNull(type2, { length } = this.nextFieldNode()) {
      return makeData({ type: type2, length });
    }
    visitBool(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitInt(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitFloat(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitUtf8(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), valueOffsets: this.readOffsets(type2), data: this.readData(type2) });
    }
    visitBinary(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), valueOffsets: this.readOffsets(type2), data: this.readData(type2) });
    }
    visitFixedSizeBinary(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitDate(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitTimestamp(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitTime(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitDecimal(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitList(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), valueOffsets: this.readOffsets(type2), "child": this.visit(type2.children[0]) });
    }
    visitStruct(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), children: this.visitMany(type2.children) });
    }
    visitUnion(type2) {
      return type2.mode === UnionMode.Sparse ? this.visitSparseUnion(type2) : this.visitDenseUnion(type2);
    }
    visitDenseUnion(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), typeIds: this.readTypeIds(type2), valueOffsets: this.readOffsets(type2), children: this.visitMany(type2.children) });
    }
    visitSparseUnion(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), typeIds: this.readTypeIds(type2), children: this.visitMany(type2.children) });
    }
    visitDictionary(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2.indices), dictionary: this.readDictionary(type2) });
    }
    visitInterval(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), data: this.readData(type2) });
    }
    visitFixedSizeList(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), "child": this.visit(type2.children[0]) });
    }
    visitMap(type2, { length, nullCount } = this.nextFieldNode()) {
      return makeData({ type: type2, length, nullCount, nullBitmap: this.readNullBitmap(type2, nullCount), valueOffsets: this.readOffsets(type2), "child": this.visit(type2.children[0]) });
    }
    nextFieldNode() {
      return this.nodes[++this.nodesIndex];
    }
    nextBufferRange() {
      return this.buffers[++this.buffersIndex];
    }
    readNullBitmap(type2, nullCount, buffer = this.nextBufferRange()) {
      return nullCount > 0 && this.readData(type2, buffer) || new Uint8Array(0);
    }
    readOffsets(type2, buffer) {
      return this.readData(type2, buffer);
    }
    readTypeIds(type2, buffer) {
      return this.readData(type2, buffer);
    }
    readData(_type, { length, offset } = this.nextBufferRange()) {
      return this.bytes.subarray(offset, offset + length);
    }
    readDictionary(type2) {
      return this.dictionaries.get(type2.id);
    }
  };
  var JSONVectorLoader = class extends VectorLoader {
    constructor(sources, nodes, buffers, dictionaries) {
      super(new Uint8Array(0), nodes, buffers, dictionaries);
      this.sources = sources;
    }
    readNullBitmap(_type, nullCount, { offset } = this.nextBufferRange()) {
      return nullCount <= 0 ? new Uint8Array(0) : packBools(this.sources[offset]);
    }
    readOffsets(_type, { offset } = this.nextBufferRange()) {
      return toArrayBufferView(Uint8Array, toArrayBufferView(Int32Array, this.sources[offset]));
    }
    readTypeIds(type2, { offset } = this.nextBufferRange()) {
      return toArrayBufferView(Uint8Array, toArrayBufferView(type2.ArrayType, this.sources[offset]));
    }
    readData(type2, { offset } = this.nextBufferRange()) {
      const { sources } = this;
      if (DataType.isTimestamp(type2)) {
        return toArrayBufferView(Uint8Array, Int642.convertArray(sources[offset]));
      } else if ((DataType.isInt(type2) || DataType.isTime(type2)) && type2.bitWidth === 64) {
        return toArrayBufferView(Uint8Array, Int642.convertArray(sources[offset]));
      } else if (DataType.isDate(type2) && type2.unit === DateUnit.MILLISECOND) {
        return toArrayBufferView(Uint8Array, Int642.convertArray(sources[offset]));
      } else if (DataType.isDecimal(type2)) {
        return toArrayBufferView(Uint8Array, Int128.convertArray(sources[offset]));
      } else if (DataType.isBinary(type2) || DataType.isFixedSizeBinary(type2)) {
        return binaryDataFromJSON(sources[offset]);
      } else if (DataType.isBool(type2)) {
        return packBools(sources[offset]);
      } else if (DataType.isUtf8(type2)) {
        return encodeUtf8(sources[offset].join(""));
      }
      return toArrayBufferView(Uint8Array, toArrayBufferView(type2.ArrayType, sources[offset].map((x) => +x)));
    }
  };
  function binaryDataFromJSON(values) {
    const joined = values.join("");
    const data = new Uint8Array(joined.length / 2);
    for (let i = 0; i < joined.length; i += 2) {
      data[i >> 1] = Number.parseInt(joined.slice(i, i + 2), 16);
    }
    return data;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/binary.mjs
  var BinaryBuilder = class extends VariableWidthBuilder {
    constructor(opts) {
      super(opts);
      this._values = new BufferBuilder(new Uint8Array(0));
    }
    get byteLength() {
      let size = this._pendingLength + this.length * 4;
      this._offsets && (size += this._offsets.byteLength);
      this._values && (size += this._values.byteLength);
      this._nulls && (size += this._nulls.byteLength);
      return size;
    }
    setValue(index, value) {
      return super.setValue(index, toUint8Array(value));
    }
    _flushPending(pending, pendingLength) {
      const offsets = this._offsets;
      const data = this._values.reserve(pendingLength).buffer;
      let offset = 0;
      for (const [index, value] of pending) {
        if (value === void 0) {
          offsets.set(index, 0);
        } else {
          const length = value.length;
          data.set(value, offset);
          offsets.set(index, length);
          offset += length;
        }
      }
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/bool.mjs
  var BoolBuilder = class extends Builder {
    constructor(options) {
      super(options);
      this._values = new BitmapBufferBuilder();
    }
    setValue(index, value) {
      this._values.set(index, +value);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/date.mjs
  var DateBuilder = class extends FixedWidthBuilder {
  };
  DateBuilder.prototype._setValue = setDate;
  var DateDayBuilder = class extends DateBuilder {
  };
  DateDayBuilder.prototype._setValue = setDateDay;
  var DateMillisecondBuilder = class extends DateBuilder {
  };
  DateMillisecondBuilder.prototype._setValue = setDateMillisecond;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/decimal.mjs
  var DecimalBuilder = class extends FixedWidthBuilder {
  };
  DecimalBuilder.prototype._setValue = setDecimal;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/dictionary.mjs
  var DictionaryBuilder = class extends Builder {
    constructor({ "type": type2, "nullValues": nulls, "dictionaryHashFunction": hashFn }) {
      super({ type: new Dictionary(type2.dictionary, type2.indices, type2.id, type2.isOrdered) });
      this._nulls = null;
      this._dictionaryOffset = 0;
      this._keysToIndices = /* @__PURE__ */ Object.create(null);
      this.indices = makeBuilder({ "type": this.type.indices, "nullValues": nulls });
      this.dictionary = makeBuilder({ "type": this.type.dictionary, "nullValues": null });
      if (typeof hashFn === "function") {
        this.valueToKey = hashFn;
      }
    }
    get values() {
      return this.indices.values;
    }
    get nullCount() {
      return this.indices.nullCount;
    }
    get nullBitmap() {
      return this.indices.nullBitmap;
    }
    get byteLength() {
      return this.indices.byteLength + this.dictionary.byteLength;
    }
    get reservedLength() {
      return this.indices.reservedLength + this.dictionary.reservedLength;
    }
    get reservedByteLength() {
      return this.indices.reservedByteLength + this.dictionary.reservedByteLength;
    }
    isValid(value) {
      return this.indices.isValid(value);
    }
    setValid(index, valid) {
      const indices = this.indices;
      valid = indices.setValid(index, valid);
      this.length = indices.length;
      return valid;
    }
    setValue(index, value) {
      const keysToIndices = this._keysToIndices;
      const key = this.valueToKey(value);
      let idx = keysToIndices[key];
      if (idx === void 0) {
        keysToIndices[key] = idx = this._dictionaryOffset + this.dictionary.append(value).length - 1;
      }
      return this.indices.setValue(index, idx);
    }
    flush() {
      const type2 = this.type;
      const prev = this._dictionary;
      const curr = this.dictionary.toVector();
      const data = this.indices.flush().clone(type2);
      data.dictionary = prev ? prev.concat(curr) : curr;
      this.finished || (this._dictionaryOffset += curr.length);
      this._dictionary = data.dictionary;
      this.clear();
      return data;
    }
    finish() {
      this.indices.finish();
      this.dictionary.finish();
      this._dictionaryOffset = 0;
      this._keysToIndices = /* @__PURE__ */ Object.create(null);
      return super.finish();
    }
    clear() {
      this.indices.clear();
      this.dictionary.clear();
      return super.clear();
    }
    valueToKey(val) {
      return typeof val === "string" ? val : `${val}`;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/fixedsizebinary.mjs
  var FixedSizeBinaryBuilder = class extends FixedWidthBuilder {
  };
  FixedSizeBinaryBuilder.prototype._setValue = setFixedSizeBinary;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/fixedsizelist.mjs
  var FixedSizeListBuilder = class extends Builder {
    setValue(index, value) {
      const [child] = this.children;
      const start = index * this.stride;
      for (let i = -1, n = value.length; ++i < n; ) {
        child.set(start + i, value[i]);
      }
    }
    addChild(child, name = "0") {
      if (this.numChildren > 0) {
        throw new Error("FixedSizeListBuilder can only have one child.");
      }
      const childIndex = this.children.push(child);
      this.type = new FixedSizeList(this.type.listSize, new Field2(name, child.type, true));
      return childIndex;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/float.mjs
  var FloatBuilder = class extends FixedWidthBuilder {
    setValue(index, value) {
      this._values.set(index, value);
    }
  };
  var Float16Builder = class extends FloatBuilder {
    setValue(index, value) {
      super.setValue(index, float64ToUint16(value));
    }
  };
  var Float32Builder = class extends FloatBuilder {
  };
  var Float64Builder = class extends FloatBuilder {
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/interval.mjs
  var IntervalBuilder = class extends FixedWidthBuilder {
  };
  IntervalBuilder.prototype._setValue = setIntervalValue;
  var IntervalDayTimeBuilder = class extends IntervalBuilder {
  };
  IntervalDayTimeBuilder.prototype._setValue = setIntervalDayTime;
  var IntervalYearMonthBuilder = class extends IntervalBuilder {
  };
  IntervalYearMonthBuilder.prototype._setValue = setIntervalYearMonth;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/int.mjs
  var IntBuilder = class extends FixedWidthBuilder {
    setValue(index, value) {
      this._values.set(index, value);
    }
  };
  var Int8Builder = class extends IntBuilder {
  };
  var Int16Builder = class extends IntBuilder {
  };
  var Int32Builder = class extends IntBuilder {
  };
  var Int64Builder = class extends IntBuilder {
  };
  var Uint8Builder = class extends IntBuilder {
  };
  var Uint16Builder = class extends IntBuilder {
  };
  var Uint32Builder = class extends IntBuilder {
  };
  var Uint64Builder = class extends IntBuilder {
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/list.mjs
  var ListBuilder = class extends VariableWidthBuilder {
    constructor(opts) {
      super(opts);
      this._offsets = new OffsetsBufferBuilder();
    }
    addChild(child, name = "0") {
      if (this.numChildren > 0) {
        throw new Error("ListBuilder can only have one child.");
      }
      this.children[this.numChildren] = child;
      this.type = new List(new Field2(name, child.type, true));
      return this.numChildren - 1;
    }
    _flushPending(pending) {
      const offsets = this._offsets;
      const [child] = this.children;
      for (const [index, value] of pending) {
        if (typeof value === "undefined") {
          offsets.set(index, 0);
        } else {
          const n = value.length;
          const start = offsets.set(index, n).buffer[index];
          for (let i = -1; ++i < n; ) {
            child.set(start + i, value[i]);
          }
        }
      }
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/map.mjs
  var MapBuilder = class extends VariableWidthBuilder {
    set(index, value) {
      return super.set(index, value);
    }
    setValue(index, value) {
      const row = value instanceof Map ? value : new Map(Object.entries(value));
      const pending = this._pending || (this._pending = /* @__PURE__ */ new Map());
      const current = pending.get(index);
      current && (this._pendingLength -= current.size);
      this._pendingLength += row.size;
      pending.set(index, row);
    }
    addChild(child, name = `${this.numChildren}`) {
      if (this.numChildren > 0) {
        throw new Error("ListBuilder can only have one child.");
      }
      this.children[this.numChildren] = child;
      this.type = new Map_(new Field2(name, child.type, true), this.type.keysSorted);
      return this.numChildren - 1;
    }
    _flushPending(pending) {
      const offsets = this._offsets;
      const [child] = this.children;
      for (const [index, value] of pending) {
        if (value === void 0) {
          offsets.set(index, 0);
        } else {
          let { [index]: idx, [index + 1]: end } = offsets.set(index, value.size).buffer;
          for (const val of value.entries()) {
            child.set(idx, val);
            if (++idx >= end)
              break;
          }
        }
      }
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/null.mjs
  var NullBuilder = class extends Builder {
    // @ts-ignore
    setValue(index, value) {
    }
    setValid(index, valid) {
      this.length = Math.max(index + 1, this.length);
      return valid;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/struct.mjs
  var StructBuilder = class extends Builder {
    setValue(index, value) {
      const { children, type: type2 } = this;
      switch (Array.isArray(value) || value.constructor) {
        case true:
          return type2.children.forEach((_, i) => children[i].set(index, value[i]));
        case Map:
          return type2.children.forEach((f, i) => children[i].set(index, value.get(f.name)));
        default:
          return type2.children.forEach((f, i) => children[i].set(index, value[f.name]));
      }
    }
    /** @inheritdoc */
    setValid(index, valid) {
      if (!super.setValid(index, valid)) {
        this.children.forEach((child) => child.setValid(index, valid));
      }
      return valid;
    }
    addChild(child, name = `${this.numChildren}`) {
      const childIndex = this.children.push(child);
      this.type = new Struct([...this.type.children, new Field2(name, child.type, true)]);
      return childIndex;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/timestamp.mjs
  var TimestampBuilder = class extends FixedWidthBuilder {
  };
  TimestampBuilder.prototype._setValue = setTimestamp;
  var TimestampSecondBuilder = class extends TimestampBuilder {
  };
  TimestampSecondBuilder.prototype._setValue = setTimestampSecond;
  var TimestampMillisecondBuilder = class extends TimestampBuilder {
  };
  TimestampMillisecondBuilder.prototype._setValue = setTimestampMillisecond;
  var TimestampMicrosecondBuilder = class extends TimestampBuilder {
  };
  TimestampMicrosecondBuilder.prototype._setValue = setTimestampMicrosecond;
  var TimestampNanosecondBuilder = class extends TimestampBuilder {
  };
  TimestampNanosecondBuilder.prototype._setValue = setTimestampNanosecond;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/time.mjs
  var TimeBuilder = class extends FixedWidthBuilder {
  };
  TimeBuilder.prototype._setValue = setTime;
  var TimeSecondBuilder = class extends TimeBuilder {
  };
  TimeSecondBuilder.prototype._setValue = setTimeSecond;
  var TimeMillisecondBuilder = class extends TimeBuilder {
  };
  TimeMillisecondBuilder.prototype._setValue = setTimeMillisecond;
  var TimeMicrosecondBuilder = class extends TimeBuilder {
  };
  TimeMicrosecondBuilder.prototype._setValue = setTimeMicrosecond;
  var TimeNanosecondBuilder = class extends TimeBuilder {
  };
  TimeNanosecondBuilder.prototype._setValue = setTimeNanosecond;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/union.mjs
  var UnionBuilder = class extends Builder {
    constructor(options) {
      super(options);
      this._typeIds = new DataBufferBuilder(new Int8Array(0), 1);
      if (typeof options["valueToChildTypeId"] === "function") {
        this._valueToChildTypeId = options["valueToChildTypeId"];
      }
    }
    get typeIdToChildIndex() {
      return this.type.typeIdToChildIndex;
    }
    append(value, childTypeId) {
      return this.set(this.length, value, childTypeId);
    }
    set(index, value, childTypeId) {
      if (childTypeId === void 0) {
        childTypeId = this._valueToChildTypeId(this, value, index);
      }
      if (this.setValid(index, this.isValid(value))) {
        this.setValue(index, value, childTypeId);
      }
      return this;
    }
    setValue(index, value, childTypeId) {
      this._typeIds.set(index, childTypeId);
      const childIndex = this.type.typeIdToChildIndex[childTypeId];
      const child = this.children[childIndex];
      child === null || child === void 0 ? void 0 : child.set(index, value);
    }
    addChild(child, name = `${this.children.length}`) {
      const childTypeId = this.children.push(child);
      const { type: { children, mode, typeIds } } = this;
      const fields = [...children, new Field2(name, child.type)];
      this.type = new Union_(mode, [...typeIds, childTypeId], fields);
      return childTypeId;
    }
    /** @ignore */
    // @ts-ignore
    _valueToChildTypeId(builder, value, offset) {
      throw new Error(`Cannot map UnionBuilder value to child typeId. Pass the \`childTypeId\` as the second argument to unionBuilder.append(), or supply a \`valueToChildTypeId\` function as part of the UnionBuilder constructor options.`);
    }
  };
  var SparseUnionBuilder = class extends UnionBuilder {
  };
  var DenseUnionBuilder = class extends UnionBuilder {
    constructor(options) {
      super(options);
      this._offsets = new DataBufferBuilder(new Int32Array(0));
    }
    /** @ignore */
    setValue(index, value, childTypeId) {
      const id = this._typeIds.set(index, childTypeId).buffer[index];
      const child = this.getChildAt(this.type.typeIdToChildIndex[id]);
      const denseIndex = this._offsets.set(index, child.length).buffer[index];
      child === null || child === void 0 ? void 0 : child.set(denseIndex, value);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/builder/utf8.mjs
  var Utf8Builder = class extends VariableWidthBuilder {
    constructor(opts) {
      super(opts);
      this._values = new BufferBuilder(new Uint8Array(0));
    }
    get byteLength() {
      let size = this._pendingLength + this.length * 4;
      this._offsets && (size += this._offsets.byteLength);
      this._values && (size += this._values.byteLength);
      this._nulls && (size += this._nulls.byteLength);
      return size;
    }
    setValue(index, value) {
      return super.setValue(index, encodeUtf8(value));
    }
    // @ts-ignore
    _flushPending(pending, pendingLength) {
    }
  };
  Utf8Builder.prototype._flushPending = BinaryBuilder.prototype._flushPending;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/builderctor.mjs
  var GetBuilderCtor = class extends Visitor {
    visitNull() {
      return NullBuilder;
    }
    visitBool() {
      return BoolBuilder;
    }
    visitInt() {
      return IntBuilder;
    }
    visitInt8() {
      return Int8Builder;
    }
    visitInt16() {
      return Int16Builder;
    }
    visitInt32() {
      return Int32Builder;
    }
    visitInt64() {
      return Int64Builder;
    }
    visitUint8() {
      return Uint8Builder;
    }
    visitUint16() {
      return Uint16Builder;
    }
    visitUint32() {
      return Uint32Builder;
    }
    visitUint64() {
      return Uint64Builder;
    }
    visitFloat() {
      return FloatBuilder;
    }
    visitFloat16() {
      return Float16Builder;
    }
    visitFloat32() {
      return Float32Builder;
    }
    visitFloat64() {
      return Float64Builder;
    }
    visitUtf8() {
      return Utf8Builder;
    }
    visitBinary() {
      return BinaryBuilder;
    }
    visitFixedSizeBinary() {
      return FixedSizeBinaryBuilder;
    }
    visitDate() {
      return DateBuilder;
    }
    visitDateDay() {
      return DateDayBuilder;
    }
    visitDateMillisecond() {
      return DateMillisecondBuilder;
    }
    visitTimestamp() {
      return TimestampBuilder;
    }
    visitTimestampSecond() {
      return TimestampSecondBuilder;
    }
    visitTimestampMillisecond() {
      return TimestampMillisecondBuilder;
    }
    visitTimestampMicrosecond() {
      return TimestampMicrosecondBuilder;
    }
    visitTimestampNanosecond() {
      return TimestampNanosecondBuilder;
    }
    visitTime() {
      return TimeBuilder;
    }
    visitTimeSecond() {
      return TimeSecondBuilder;
    }
    visitTimeMillisecond() {
      return TimeMillisecondBuilder;
    }
    visitTimeMicrosecond() {
      return TimeMicrosecondBuilder;
    }
    visitTimeNanosecond() {
      return TimeNanosecondBuilder;
    }
    visitDecimal() {
      return DecimalBuilder;
    }
    visitList() {
      return ListBuilder;
    }
    visitStruct() {
      return StructBuilder;
    }
    visitUnion() {
      return UnionBuilder;
    }
    visitDenseUnion() {
      return DenseUnionBuilder;
    }
    visitSparseUnion() {
      return SparseUnionBuilder;
    }
    visitDictionary() {
      return DictionaryBuilder;
    }
    visitInterval() {
      return IntervalBuilder;
    }
    visitIntervalDayTime() {
      return IntervalDayTimeBuilder;
    }
    visitIntervalYearMonth() {
      return IntervalYearMonthBuilder;
    }
    visitFixedSizeList() {
      return FixedSizeListBuilder;
    }
    visitMap() {
      return MapBuilder;
    }
  };
  var instance6 = new GetBuilderCtor();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/typecomparator.mjs
  var TypeComparator = class extends Visitor {
    compareSchemas(schema, other) {
      return schema === other || other instanceof schema.constructor && this.compareManyFields(schema.fields, other.fields);
    }
    compareManyFields(fields, others) {
      return fields === others || Array.isArray(fields) && Array.isArray(others) && fields.length === others.length && fields.every((f, i) => this.compareFields(f, others[i]));
    }
    compareFields(field, other) {
      return field === other || other instanceof field.constructor && field.name === other.name && field.nullable === other.nullable && this.visit(field.type, other.type);
    }
  };
  function compareConstructor(type2, other) {
    return other instanceof type2.constructor;
  }
  function compareAny(type2, other) {
    return type2 === other || compareConstructor(type2, other);
  }
  function compareInt(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.bitWidth === other.bitWidth && type2.isSigned === other.isSigned;
  }
  function compareFloat(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.precision === other.precision;
  }
  function compareFixedSizeBinary(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.byteWidth === other.byteWidth;
  }
  function compareDate(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.unit === other.unit;
  }
  function compareTimestamp(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.unit === other.unit && type2.timezone === other.timezone;
  }
  function compareTime(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.unit === other.unit && type2.bitWidth === other.bitWidth;
  }
  function compareList(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.children.length === other.children.length && instance7.compareManyFields(type2.children, other.children);
  }
  function compareStruct(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.children.length === other.children.length && instance7.compareManyFields(type2.children, other.children);
  }
  function compareUnion(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.mode === other.mode && type2.typeIds.every((x, i) => x === other.typeIds[i]) && instance7.compareManyFields(type2.children, other.children);
  }
  function compareDictionary(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.id === other.id && type2.isOrdered === other.isOrdered && instance7.visit(type2.indices, other.indices) && instance7.visit(type2.dictionary, other.dictionary);
  }
  function compareInterval(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.unit === other.unit;
  }
  function compareFixedSizeList(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.listSize === other.listSize && type2.children.length === other.children.length && instance7.compareManyFields(type2.children, other.children);
  }
  function compareMap(type2, other) {
    return type2 === other || compareConstructor(type2, other) && type2.keysSorted === other.keysSorted && type2.children.length === other.children.length && instance7.compareManyFields(type2.children, other.children);
  }
  TypeComparator.prototype.visitNull = compareAny;
  TypeComparator.prototype.visitBool = compareAny;
  TypeComparator.prototype.visitInt = compareInt;
  TypeComparator.prototype.visitInt8 = compareInt;
  TypeComparator.prototype.visitInt16 = compareInt;
  TypeComparator.prototype.visitInt32 = compareInt;
  TypeComparator.prototype.visitInt64 = compareInt;
  TypeComparator.prototype.visitUint8 = compareInt;
  TypeComparator.prototype.visitUint16 = compareInt;
  TypeComparator.prototype.visitUint32 = compareInt;
  TypeComparator.prototype.visitUint64 = compareInt;
  TypeComparator.prototype.visitFloat = compareFloat;
  TypeComparator.prototype.visitFloat16 = compareFloat;
  TypeComparator.prototype.visitFloat32 = compareFloat;
  TypeComparator.prototype.visitFloat64 = compareFloat;
  TypeComparator.prototype.visitUtf8 = compareAny;
  TypeComparator.prototype.visitBinary = compareAny;
  TypeComparator.prototype.visitFixedSizeBinary = compareFixedSizeBinary;
  TypeComparator.prototype.visitDate = compareDate;
  TypeComparator.prototype.visitDateDay = compareDate;
  TypeComparator.prototype.visitDateMillisecond = compareDate;
  TypeComparator.prototype.visitTimestamp = compareTimestamp;
  TypeComparator.prototype.visitTimestampSecond = compareTimestamp;
  TypeComparator.prototype.visitTimestampMillisecond = compareTimestamp;
  TypeComparator.prototype.visitTimestampMicrosecond = compareTimestamp;
  TypeComparator.prototype.visitTimestampNanosecond = compareTimestamp;
  TypeComparator.prototype.visitTime = compareTime;
  TypeComparator.prototype.visitTimeSecond = compareTime;
  TypeComparator.prototype.visitTimeMillisecond = compareTime;
  TypeComparator.prototype.visitTimeMicrosecond = compareTime;
  TypeComparator.prototype.visitTimeNanosecond = compareTime;
  TypeComparator.prototype.visitDecimal = compareAny;
  TypeComparator.prototype.visitList = compareList;
  TypeComparator.prototype.visitStruct = compareStruct;
  TypeComparator.prototype.visitUnion = compareUnion;
  TypeComparator.prototype.visitDenseUnion = compareUnion;
  TypeComparator.prototype.visitSparseUnion = compareUnion;
  TypeComparator.prototype.visitDictionary = compareDictionary;
  TypeComparator.prototype.visitInterval = compareInterval;
  TypeComparator.prototype.visitIntervalDayTime = compareInterval;
  TypeComparator.prototype.visitIntervalYearMonth = compareInterval;
  TypeComparator.prototype.visitFixedSizeList = compareFixedSizeList;
  TypeComparator.prototype.visitMap = compareMap;
  var instance7 = new TypeComparator();
  function compareSchemas(schema, other) {
    return instance7.compareSchemas(schema, other);
  }
  function compareFields(field, other) {
    return instance7.compareFields(field, other);
  }
  function compareTypes(type2, other) {
    return instance7.visit(type2, other);
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/factories.mjs
  function makeBuilder(options) {
    const type2 = options.type;
    const builder = new (instance6.getVisitFn(type2)())(options);
    if (type2.children && type2.children.length > 0) {
      const children = options["children"] || [];
      const defaultOptions = { "nullValues": options["nullValues"] };
      const getChildOptions = Array.isArray(children) ? (_, i) => children[i] || defaultOptions : ({ name }) => children[name] || defaultOptions;
      for (const [index, field] of type2.children.entries()) {
        const { type: type3 } = field;
        const opts = getChildOptions(field, index);
        builder.children.push(makeBuilder(Object.assign(Object.assign({}, opts), { type: type3 })));
      }
    }
    return builder;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/util/recordbatch.mjs
  function distributeVectorsIntoRecordBatches(schema, vecs) {
    return uniformlyDistributeChunksAcrossRecordBatches(schema, vecs.map((v) => v.data.concat()));
  }
  function uniformlyDistributeChunksAcrossRecordBatches(schema, cols) {
    const fields = [...schema.fields];
    const batches = [];
    const memo = { numBatches: cols.reduce((n, c) => Math.max(n, c.length), 0) };
    let numBatches = 0, batchLength = 0;
    let i = -1;
    const numColumns = cols.length;
    let child, children = [];
    while (memo.numBatches-- > 0) {
      for (batchLength = Number.POSITIVE_INFINITY, i = -1; ++i < numColumns; ) {
        children[i] = child = cols[i].shift();
        batchLength = Math.min(batchLength, child ? child.length : batchLength);
      }
      if (Number.isFinite(batchLength)) {
        children = distributeChildren(fields, batchLength, children, cols, memo);
        if (batchLength > 0) {
          batches[numBatches++] = makeData({
            type: new Struct(fields),
            length: batchLength,
            nullCount: 0,
            children: children.slice()
          });
        }
      }
    }
    return [
      schema = schema.assign(fields),
      batches.map((data) => new RecordBatch(schema, data))
    ];
  }
  function distributeChildren(fields, batchLength, children, columns, memo) {
    var _a5;
    const nullBitmapSize = (batchLength + 63 & ~63) >> 3;
    for (let i = -1, n = columns.length; ++i < n; ) {
      const child = children[i];
      const length = child === null || child === void 0 ? void 0 : child.length;
      if (length >= batchLength) {
        if (length === batchLength) {
          children[i] = child;
        } else {
          children[i] = child.slice(0, batchLength);
          memo.numBatches = Math.max(memo.numBatches, columns[i].unshift(child.slice(batchLength, length - batchLength)));
        }
      } else {
        const field = fields[i];
        fields[i] = field.clone({ nullable: true });
        children[i] = (_a5 = child === null || child === void 0 ? void 0 : child._changeLengthAndBackfillNullBitmap(batchLength)) !== null && _a5 !== void 0 ? _a5 : makeData({
          type: field.type,
          length: batchLength,
          nullCount: batchLength,
          nullBitmap: new Uint8Array(nullBitmapSize)
        });
      }
    }
    return children;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/table.mjs
  var _a3;
  var Table = class _Table {
    constructor(...args) {
      var _b2, _c2;
      if (args.length === 0) {
        this.batches = [];
        this.schema = new Schema2([]);
        this._offsets = [0];
        return this;
      }
      let schema;
      let offsets;
      if (args[0] instanceof Schema2) {
        schema = args.shift();
      }
      if (args[args.length - 1] instanceof Uint32Array) {
        offsets = args.pop();
      }
      const unwrap = (x) => {
        if (x) {
          if (x instanceof RecordBatch) {
            return [x];
          } else if (x instanceof _Table) {
            return x.batches;
          } else if (x instanceof Data) {
            if (x.type instanceof Struct) {
              return [new RecordBatch(new Schema2(x.type.children), x)];
            }
          } else if (Array.isArray(x)) {
            return x.flatMap((v) => unwrap(v));
          } else if (typeof x[Symbol.iterator] === "function") {
            return [...x].flatMap((v) => unwrap(v));
          } else if (typeof x === "object") {
            const keys = Object.keys(x);
            const vecs = keys.map((k) => new Vector([x[k]]));
            const schema2 = new Schema2(keys.map((k, i) => new Field2(String(k), vecs[i].type)));
            const [, batches2] = distributeVectorsIntoRecordBatches(schema2, vecs);
            return batches2.length === 0 ? [new RecordBatch(x)] : batches2;
          }
        }
        return [];
      };
      const batches = args.flatMap((v) => unwrap(v));
      schema = (_c2 = schema !== null && schema !== void 0 ? schema : (_b2 = batches[0]) === null || _b2 === void 0 ? void 0 : _b2.schema) !== null && _c2 !== void 0 ? _c2 : new Schema2([]);
      if (!(schema instanceof Schema2)) {
        throw new TypeError("Table constructor expects a [Schema, RecordBatch[]] pair.");
      }
      for (const batch of batches) {
        if (!(batch instanceof RecordBatch)) {
          throw new TypeError("Table constructor expects a [Schema, RecordBatch[]] pair.");
        }
        if (!compareSchemas(schema, batch.schema)) {
          throw new TypeError("Table and inner RecordBatch schemas must be equivalent.");
        }
      }
      this.schema = schema;
      this.batches = batches;
      this._offsets = offsets !== null && offsets !== void 0 ? offsets : computeChunkOffsets(this.data);
    }
    /**
     * The contiguous {@link RecordBatch `RecordBatch`} chunks of the Table rows.
     */
    get data() {
      return this.batches.map(({ data }) => data);
    }
    /**
     * The number of columns in this Table.
     */
    get numCols() {
      return this.schema.fields.length;
    }
    /**
     * The number of rows in this Table.
     */
    get numRows() {
      return this.data.reduce((numRows, data) => numRows + data.length, 0);
    }
    /**
     * The number of null rows in this Table.
     */
    get nullCount() {
      if (this._nullCount === -1) {
        this._nullCount = computeChunkNullCounts(this.data);
      }
      return this._nullCount;
    }
    /**
     * Check whether an element is null.
     *
     * @param index The index at which to read the validity bitmap.
     */
    // @ts-ignore
    isValid(index) {
      return false;
    }
    /**
     * Get an element value by position.
     *
     * @param index The index of the element to read.
     */
    // @ts-ignore
    get(index) {
      return null;
    }
    /**
     * Set an element value by position.
     *
     * @param index The index of the element to write.
     * @param value The value to set.
     */
    // @ts-ignore
    set(index, value) {
      return;
    }
    /**
     * Retrieve the index of the first occurrence of a value in an Vector.
     *
     * @param element The value to locate in the Vector.
     * @param offset The index at which to begin the search. If offset is omitted, the search starts at index 0.
     */
    // @ts-ignore
    indexOf(element, offset) {
      return -1;
    }
    /**
     * Get the size in bytes of an element by index.
     * @param index The index at which to get the byteLength.
     */
    // @ts-ignore
    getByteLength(index) {
      return 0;
    }
    /**
     * Iterator for rows in this Table.
     */
    [Symbol.iterator]() {
      if (this.batches.length > 0) {
        return instance4.visit(new Vector(this.data));
      }
      return new Array(0)[Symbol.iterator]();
    }
    /**
     * Return a JavaScript Array of the Table rows.
     *
     * @returns An Array of Table rows.
     */
    toArray() {
      return [...this];
    }
    /**
     * Returns a string representation of the Table rows.
     *
     * @returns A string representation of the Table rows.
     */
    toString() {
      return `[
  ${this.toArray().join(",\n  ")}
]`;
    }
    /**
     * Combines two or more Tables of the same schema.
     *
     * @param others Additional Tables to add to the end of this Tables.
     */
    concat(...others) {
      const schema = this.schema;
      const data = this.data.concat(others.flatMap(({ data: data2 }) => data2));
      return new _Table(schema, data.map((data2) => new RecordBatch(schema, data2)));
    }
    /**
     * Return a zero-copy sub-section of this Table.
     *
     * @param begin The beginning of the specified portion of the Table.
     * @param end The end of the specified portion of the Table. This is exclusive of the element at the index 'end'.
     */
    slice(begin, end) {
      const schema = this.schema;
      [begin, end] = clampRange({ length: this.numRows }, begin, end);
      const data = sliceChunks(this.data, this._offsets, begin, end);
      return new _Table(schema, data.map((chunk) => new RecordBatch(schema, chunk)));
    }
    /**
     * Returns a child Vector by name, or null if this Vector has no child with the given name.
     *
     * @param name The name of the child to retrieve.
     */
    getChild(name) {
      return this.getChildAt(this.schema.fields.findIndex((f) => f.name === name));
    }
    /**
     * Returns a child Vector by index, or null if this Vector has no child at the supplied index.
     *
     * @param index The index of the child to retrieve.
     */
    getChildAt(index) {
      if (index > -1 && index < this.schema.fields.length) {
        const data = this.data.map((data2) => data2.children[index]);
        if (data.length === 0) {
          const { type: type2 } = this.schema.fields[index];
          const empty = makeData({ type: type2, length: 0, nullCount: 0 });
          data.push(empty._changeLengthAndBackfillNullBitmap(this.numRows));
        }
        return new Vector(data);
      }
      return null;
    }
    /**
     * Sets a child Vector by name.
     *
     * @param name The name of the child to overwrite.
     * @returns A new Table with the supplied child for the specified name.
     */
    setChild(name, child) {
      var _b2;
      return this.setChildAt((_b2 = this.schema.fields) === null || _b2 === void 0 ? void 0 : _b2.findIndex((f) => f.name === name), child);
    }
    setChildAt(index, child) {
      let schema = this.schema;
      let batches = [...this.batches];
      if (index > -1 && index < this.numCols) {
        if (!child) {
          child = new Vector([makeData({ type: new Null(), length: this.numRows })]);
        }
        const fields = schema.fields.slice();
        const field = fields[index].clone({ type: child.type });
        const children = this.schema.fields.map((_, i) => this.getChildAt(i));
        [fields[index], children[index]] = [field, child];
        [schema, batches] = distributeVectorsIntoRecordBatches(schema, children);
      }
      return new _Table(schema, batches);
    }
    /**
     * Construct a new Table containing only specified columns.
     *
     * @param columnNames Names of columns to keep.
     * @returns A new Table of columns matching the specified names.
     */
    select(columnNames) {
      const nameToIndex = this.schema.fields.reduce((m, f, i) => m.set(f.name, i), /* @__PURE__ */ new Map());
      return this.selectAt(columnNames.map((columnName) => nameToIndex.get(columnName)).filter((x) => x > -1));
    }
    /**
     * Construct a new Table containing only columns at the specified indices.
     *
     * @param columnIndices Indices of columns to keep.
     * @returns A new Table of columns at the specified indices.
     */
    selectAt(columnIndices) {
      const schema = this.schema.selectAt(columnIndices);
      const data = this.batches.map((batch) => batch.selectAt(columnIndices));
      return new _Table(schema, data);
    }
    assign(other) {
      const fields = this.schema.fields;
      const [indices, oldToNew] = other.schema.fields.reduce((memo, f2, newIdx) => {
        const [indices2, oldToNew2] = memo;
        const i = fields.findIndex((f) => f.name === f2.name);
        ~i ? oldToNew2[i] = newIdx : indices2.push(newIdx);
        return memo;
      }, [[], []]);
      const schema = this.schema.assign(other.schema);
      const columns = [
        ...fields.map((_, i) => [i, oldToNew[i]]).map(([i, j]) => j === void 0 ? this.getChildAt(i) : other.getChildAt(j)),
        ...indices.map((i) => other.getChildAt(i))
      ].filter(Boolean);
      return new _Table(...distributeVectorsIntoRecordBatches(schema, columns));
    }
  };
  _a3 = Symbol.toStringTag;
  Table[_a3] = ((proto) => {
    proto.schema = null;
    proto.batches = [];
    proto._offsets = new Uint32Array([0]);
    proto._nullCount = -1;
    proto[Symbol.isConcatSpreadable] = true;
    proto["isValid"] = wrapChunkedCall1(isChunkedValid);
    proto["get"] = wrapChunkedCall1(instance2.getVisitFn(Type.Struct));
    proto["set"] = wrapChunkedCall2(instance.getVisitFn(Type.Struct));
    proto["indexOf"] = wrapChunkedIndexOf(instance3.getVisitFn(Type.Struct));
    proto["getByteLength"] = wrapChunkedCall1(instance5.getVisitFn(Type.Struct));
    return "Table";
  })(Table.prototype);

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/recordbatch.mjs
  var _a4;
  var RecordBatch = class _RecordBatch {
    constructor(...args) {
      switch (args.length) {
        case 2: {
          [this.schema] = args;
          if (!(this.schema instanceof Schema2)) {
            throw new TypeError("RecordBatch constructor expects a [Schema, Data] pair.");
          }
          [
            ,
            this.data = makeData({
              nullCount: 0,
              type: new Struct(this.schema.fields),
              children: this.schema.fields.map((f) => makeData({ type: f.type, nullCount: 0 }))
            })
          ] = args;
          if (!(this.data instanceof Data)) {
            throw new TypeError("RecordBatch constructor expects a [Schema, Data] pair.");
          }
          [this.schema, this.data] = ensureSameLengthData(this.schema, this.data.children);
          break;
        }
        case 1: {
          const [obj] = args;
          const { fields, children, length } = Object.keys(obj).reduce((memo, name, i) => {
            memo.children[i] = obj[name];
            memo.length = Math.max(memo.length, obj[name].length);
            memo.fields[i] = Field2.new({ name, type: obj[name].type, nullable: true });
            return memo;
          }, {
            length: 0,
            fields: new Array(),
            children: new Array()
          });
          const schema = new Schema2(fields);
          const data = makeData({ type: new Struct(fields), length, children, nullCount: 0 });
          [this.schema, this.data] = ensureSameLengthData(schema, data.children, length);
          break;
        }
        default:
          throw new TypeError("RecordBatch constructor expects an Object mapping names to child Data, or a [Schema, Data] pair.");
      }
    }
    get dictionaries() {
      return this._dictionaries || (this._dictionaries = collectDictionaries(this.schema.fields, this.data.children));
    }
    /**
     * The number of columns in this RecordBatch.
     */
    get numCols() {
      return this.schema.fields.length;
    }
    /**
     * The number of rows in this RecordBatch.
     */
    get numRows() {
      return this.data.length;
    }
    /**
     * The number of null rows in this RecordBatch.
     */
    get nullCount() {
      return this.data.nullCount;
    }
    /**
     * Check whether an element is null.
     * @param index The index at which to read the validity bitmap.
     */
    isValid(index) {
      return this.data.getValid(index);
    }
    /**
     * Get a row by position.
     * @param index The index of the element to read.
     */
    get(index) {
      return instance2.visit(this.data, index);
    }
    /**
     * Set a row by position.
     * @param index The index of the element to write.
     * @param value The value to set.
     */
    set(index, value) {
      return instance.visit(this.data, index, value);
    }
    /**
     * Retrieve the index of the first occurrence of a row in an RecordBatch.
     * @param element The row to locate in the RecordBatch.
     * @param offset The index at which to begin the search. If offset is omitted, the search starts at index 0.
     */
    indexOf(element, offset) {
      return instance3.visit(this.data, element, offset);
    }
    /**
     * Get the size (in bytes) of a row by index.
     * @param index The row index for which to compute the byteLength.
     */
    getByteLength(index) {
      return instance5.visit(this.data, index);
    }
    /**
     * Iterator for rows in this RecordBatch.
     */
    [Symbol.iterator]() {
      return instance4.visit(new Vector([this.data]));
    }
    /**
     * Return a JavaScript Array of the RecordBatch rows.
     * @returns An Array of RecordBatch rows.
     */
    toArray() {
      return [...this];
    }
    /**
     * Combines two or more RecordBatch of the same schema.
     * @param others Additional RecordBatch to add to the end of this RecordBatch.
     */
    concat(...others) {
      return new Table(this.schema, [this, ...others]);
    }
    /**
     * Return a zero-copy sub-section of this RecordBatch.
     * @param start The beginning of the specified portion of the RecordBatch.
     * @param end The end of the specified portion of the RecordBatch. This is exclusive of the element at the index 'end'.
     */
    slice(begin, end) {
      const [slice] = new Vector([this.data]).slice(begin, end).data;
      return new _RecordBatch(this.schema, slice);
    }
    /**
     * Returns a child Vector by name, or null if this Vector has no child with the given name.
     * @param name The name of the child to retrieve.
     */
    getChild(name) {
      var _b2;
      return this.getChildAt((_b2 = this.schema.fields) === null || _b2 === void 0 ? void 0 : _b2.findIndex((f) => f.name === name));
    }
    /**
     * Returns a child Vector by index, or null if this Vector has no child at the supplied index.
     * @param index The index of the child to retrieve.
     */
    getChildAt(index) {
      if (index > -1 && index < this.schema.fields.length) {
        return new Vector([this.data.children[index]]);
      }
      return null;
    }
    /**
     * Sets a child Vector by name.
     * @param name The name of the child to overwrite.
     * @returns A new RecordBatch with the new child for the specified name.
     */
    setChild(name, child) {
      var _b2;
      return this.setChildAt((_b2 = this.schema.fields) === null || _b2 === void 0 ? void 0 : _b2.findIndex((f) => f.name === name), child);
    }
    setChildAt(index, child) {
      let schema = this.schema;
      let data = this.data;
      if (index > -1 && index < this.numCols) {
        if (!child) {
          child = new Vector([makeData({ type: new Null(), length: this.numRows })]);
        }
        const fields = schema.fields.slice();
        const children = data.children.slice();
        const field = fields[index].clone({ type: child.type });
        [fields[index], children[index]] = [field, child.data[0]];
        schema = new Schema2(fields, new Map(this.schema.metadata));
        data = makeData({ type: new Struct(fields), children });
      }
      return new _RecordBatch(schema, data);
    }
    /**
     * Construct a new RecordBatch containing only specified columns.
     *
     * @param columnNames Names of columns to keep.
     * @returns A new RecordBatch of columns matching the specified names.
     */
    select(columnNames) {
      const schema = this.schema.select(columnNames);
      const type2 = new Struct(schema.fields);
      const children = [];
      for (const name of columnNames) {
        const index = this.schema.fields.findIndex((f) => f.name === name);
        if (~index) {
          children[index] = this.data.children[index];
        }
      }
      return new _RecordBatch(schema, makeData({ type: type2, length: this.numRows, children }));
    }
    /**
     * Construct a new RecordBatch containing only columns at the specified indices.
     *
     * @param columnIndices Indices of columns to keep.
     * @returns A new RecordBatch of columns matching at the specified indices.
     */
    selectAt(columnIndices) {
      const schema = this.schema.selectAt(columnIndices);
      const children = columnIndices.map((i) => this.data.children[i]).filter(Boolean);
      const subset = makeData({ type: new Struct(schema.fields), length: this.numRows, children });
      return new _RecordBatch(schema, subset);
    }
  };
  _a4 = Symbol.toStringTag;
  RecordBatch[_a4] = ((proto) => {
    proto._nullCount = -1;
    proto[Symbol.isConcatSpreadable] = true;
    return "RecordBatch";
  })(RecordBatch.prototype);
  function ensureSameLengthData(schema, chunks, maxLength = chunks.reduce((max, col) => Math.max(max, col.length), 0)) {
    var _b2;
    const fields = [...schema.fields];
    const children = [...chunks];
    const nullBitmapSize = (maxLength + 63 & ~63) >> 3;
    for (const [idx, field] of schema.fields.entries()) {
      const chunk = chunks[idx];
      if (!chunk || chunk.length !== maxLength) {
        fields[idx] = field.clone({ nullable: true });
        children[idx] = (_b2 = chunk === null || chunk === void 0 ? void 0 : chunk._changeLengthAndBackfillNullBitmap(maxLength)) !== null && _b2 !== void 0 ? _b2 : makeData({
          type: field.type,
          length: maxLength,
          nullCount: maxLength,
          nullBitmap: new Uint8Array(nullBitmapSize)
        });
      }
    }
    return [
      schema.assign(fields),
      makeData({ type: new Struct(fields), length: maxLength, children })
    ];
  }
  function collectDictionaries(fields, children, dictionaries = /* @__PURE__ */ new Map()) {
    for (let i = -1, n = fields.length; ++i < n; ) {
      const field = fields[i];
      const type2 = field.type;
      const data = children[i];
      if (DataType.isDictionary(type2)) {
        if (!dictionaries.has(type2.id)) {
          if (data.dictionary) {
            dictionaries.set(type2.id, data.dictionary);
          }
        } else if (dictionaries.get(type2.id) !== data.dictionary) {
          throw new Error(`Cannot create Schema containing two different dictionaries with the same Id`);
        }
      }
      if (type2.children && type2.children.length > 0) {
        collectDictionaries(type2.children, data.children, dictionaries);
      }
    }
    return dictionaries;
  }
  var _InternalEmptyPlaceholderRecordBatch = class extends RecordBatch {
    constructor(schema) {
      const children = schema.fields.map((f) => makeData({ type: f.type }));
      const data = makeData({ type: new Struct(schema.fields), nullCount: 0, children });
      super(schema, data);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/body-compression-method.mjs
  var BodyCompressionMethod;
  (function(BodyCompressionMethod2) {
    BodyCompressionMethod2[BodyCompressionMethod2["BUFFER"] = 0] = "BUFFER";
  })(BodyCompressionMethod || (BodyCompressionMethod = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/compression-type.mjs
  var CompressionType;
  (function(CompressionType2) {
    CompressionType2[CompressionType2["LZ4_FRAME"] = 0] = "LZ4_FRAME";
    CompressionType2[CompressionType2["ZSTD"] = 1] = "ZSTD";
  })(CompressionType || (CompressionType = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/body-compression.mjs
  var BodyCompression = class _BodyCompression {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsBodyCompression(bb, obj) {
      return (obj || new _BodyCompression()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsBodyCompression(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _BodyCompression()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * Compressor library.
     * For LZ4_FRAME, each compressed buffer must consist of a single frame.
     */
    codec() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt8(this.bb_pos + offset) : CompressionType.LZ4_FRAME;
    }
    /**
     * Indicates the way the record batch body was compressed
     */
    method() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.readInt8(this.bb_pos + offset) : BodyCompressionMethod.BUFFER;
    }
    static startBodyCompression(builder) {
      builder.startObject(2);
    }
    static addCodec(builder, codec) {
      builder.addFieldInt8(0, codec, CompressionType.LZ4_FRAME);
    }
    static addMethod(builder, method) {
      builder.addFieldInt8(1, method, BodyCompressionMethod.BUFFER);
    }
    static endBodyCompression(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static createBodyCompression(builder, codec, method) {
      _BodyCompression.startBodyCompression(builder);
      _BodyCompression.addCodec(builder, codec);
      _BodyCompression.addMethod(builder, method);
      return _BodyCompression.endBodyCompression(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/buffer.mjs
  var Buffer2 = class {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    /**
     * The relative offset into the shared memory page where the bytes for this
     * buffer starts
     */
    offset() {
      return this.bb.readInt64(this.bb_pos);
    }
    /**
     * The absolute length (in bytes) of the memory buffer. The memory is found
     * from offset (inclusive) to offset + length (non-inclusive). When building
     * messages using the encapsulated IPC message, padding bytes may be written
     * after a buffer, but such padding bytes do not need to be accounted for in
     * the size here.
     */
    length() {
      return this.bb.readInt64(this.bb_pos + 8);
    }
    static sizeOf() {
      return 16;
    }
    static createBuffer(builder, offset, length) {
      builder.prep(8, 16);
      builder.writeInt64(length);
      builder.writeInt64(offset);
      return builder.offset();
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/field-node.mjs
  var FieldNode = class {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    /**
     * The number of value slots in the Arrow array at this level of a nested
     * tree
     */
    length() {
      return this.bb.readInt64(this.bb_pos);
    }
    /**
     * The number of observed nulls. Fields with null_count == 0 may choose not
     * to write their physical validity bitmap out as a materialized buffer,
     * instead setting the length of the bitmap buffer to 0.
     */
    nullCount() {
      return this.bb.readInt64(this.bb_pos + 8);
    }
    static sizeOf() {
      return 16;
    }
    static createFieldNode(builder, length, null_count) {
      builder.prep(8, 16);
      builder.writeInt64(null_count);
      builder.writeInt64(length);
      return builder.offset();
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/record-batch.mjs
  var RecordBatch2 = class _RecordBatch {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsRecordBatch(bb, obj) {
      return (obj || new _RecordBatch()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsRecordBatch(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _RecordBatch()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    /**
     * number of records / rows. The arrays in the batch should all have this
     * length
     */
    length() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt64(this.bb_pos + offset) : this.bb.createLong(0, 0);
    }
    /**
     * Nodes correspond to the pre-ordered flattened logical schema
     */
    nodes(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? (obj || new FieldNode()).__init(this.bb.__vector(this.bb_pos + offset) + index * 16, this.bb) : null;
    }
    nodesLength() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    /**
     * Buffers correspond to the pre-ordered flattened buffer tree
     *
     * The number of buffers appended to this list depends on the schema. For
     * example, most primitive arrays will have 2 buffers, 1 for the validity
     * bitmap and 1 for the values. For struct arrays, there will only be a
     * single buffer for the validity (nulls) bitmap
     */
    buffers(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? (obj || new Buffer2()).__init(this.bb.__vector(this.bb_pos + offset) + index * 16, this.bb) : null;
    }
    buffersLength() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    /**
     * Optional compression of the message body
     */
    compression(obj) {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? (obj || new BodyCompression()).__init(this.bb.__indirect(this.bb_pos + offset), this.bb) : null;
    }
    static startRecordBatch(builder) {
      builder.startObject(4);
    }
    static addLength(builder, length) {
      builder.addFieldInt64(0, length, builder.createLong(0, 0));
    }
    static addNodes(builder, nodesOffset) {
      builder.addFieldOffset(1, nodesOffset, 0);
    }
    static startNodesVector(builder, numElems) {
      builder.startVector(16, numElems, 8);
    }
    static addBuffers(builder, buffersOffset) {
      builder.addFieldOffset(2, buffersOffset, 0);
    }
    static startBuffersVector(builder, numElems) {
      builder.startVector(16, numElems, 8);
    }
    static addCompression(builder, compressionOffset) {
      builder.addFieldOffset(3, compressionOffset, 0);
    }
    static endRecordBatch(builder) {
      const offset = builder.endObject();
      return offset;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/dictionary-batch.mjs
  var DictionaryBatch = class _DictionaryBatch {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsDictionaryBatch(bb, obj) {
      return (obj || new _DictionaryBatch()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsDictionaryBatch(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _DictionaryBatch()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    id() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt64(this.bb_pos + offset) : this.bb.createLong(0, 0);
    }
    data(obj) {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? (obj || new RecordBatch2()).__init(this.bb.__indirect(this.bb_pos + offset), this.bb) : null;
    }
    /**
     * If isDelta is true the values in the dictionary are to be appended to a
     * dictionary with the indicated id. If isDelta is false this dictionary
     * should replace the existing dictionary.
     */
    isDelta() {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? !!this.bb.readInt8(this.bb_pos + offset) : false;
    }
    static startDictionaryBatch(builder) {
      builder.startObject(3);
    }
    static addId(builder, id) {
      builder.addFieldInt64(0, id, builder.createLong(0, 0));
    }
    static addData(builder, dataOffset) {
      builder.addFieldOffset(1, dataOffset, 0);
    }
    static addIsDelta(builder, isDelta) {
      builder.addFieldInt8(2, +isDelta, 0);
    }
    static endDictionaryBatch(builder) {
      const offset = builder.endObject();
      return offset;
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/message-header.mjs
  var MessageHeader2;
  (function(MessageHeader3) {
    MessageHeader3[MessageHeader3["NONE"] = 0] = "NONE";
    MessageHeader3[MessageHeader3["Schema"] = 1] = "Schema";
    MessageHeader3[MessageHeader3["DictionaryBatch"] = 2] = "DictionaryBatch";
    MessageHeader3[MessageHeader3["RecordBatch"] = 3] = "RecordBatch";
    MessageHeader3[MessageHeader3["Tensor"] = 4] = "Tensor";
    MessageHeader3[MessageHeader3["SparseTensor"] = 5] = "SparseTensor";
  })(MessageHeader2 || (MessageHeader2 = {}));

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/fb/message.mjs
  var Message = class _Message {
    constructor() {
      this.bb = null;
      this.bb_pos = 0;
    }
    __init(i, bb) {
      this.bb_pos = i;
      this.bb = bb;
      return this;
    }
    static getRootAsMessage(bb, obj) {
      return (obj || new _Message()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    static getSizePrefixedRootAsMessage(bb, obj) {
      bb.setPosition(bb.position() + SIZE_PREFIX_LENGTH);
      return (obj || new _Message()).__init(bb.readInt32(bb.position()) + bb.position(), bb);
    }
    version() {
      const offset = this.bb.__offset(this.bb_pos, 4);
      return offset ? this.bb.readInt16(this.bb_pos + offset) : MetadataVersion2.V1;
    }
    headerType() {
      const offset = this.bb.__offset(this.bb_pos, 6);
      return offset ? this.bb.readUint8(this.bb_pos + offset) : MessageHeader2.NONE;
    }
    // @ts-ignore
    header(obj) {
      const offset = this.bb.__offset(this.bb_pos, 8);
      return offset ? this.bb.__union(obj, this.bb_pos + offset) : null;
    }
    bodyLength() {
      const offset = this.bb.__offset(this.bb_pos, 10);
      return offset ? this.bb.readInt64(this.bb_pos + offset) : this.bb.createLong(0, 0);
    }
    customMetadata(index, obj) {
      const offset = this.bb.__offset(this.bb_pos, 12);
      return offset ? (obj || new KeyValue()).__init(this.bb.__indirect(this.bb.__vector(this.bb_pos + offset) + index * 4), this.bb) : null;
    }
    customMetadataLength() {
      const offset = this.bb.__offset(this.bb_pos, 12);
      return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
    }
    static startMessage(builder) {
      builder.startObject(5);
    }
    static addVersion(builder, version) {
      builder.addFieldInt16(0, version, MetadataVersion2.V1);
    }
    static addHeaderType(builder, headerType) {
      builder.addFieldInt8(1, headerType, MessageHeader2.NONE);
    }
    static addHeader(builder, headerOffset) {
      builder.addFieldOffset(2, headerOffset, 0);
    }
    static addBodyLength(builder, bodyLength) {
      builder.addFieldInt64(3, bodyLength, builder.createLong(0, 0));
    }
    static addCustomMetadata(builder, customMetadataOffset) {
      builder.addFieldOffset(4, customMetadataOffset, 0);
    }
    static createCustomMetadataVector(builder, data) {
      builder.startVector(4, data.length, 4);
      for (let i = data.length - 1; i >= 0; i--) {
        builder.addOffset(data[i]);
      }
      return builder.endVector();
    }
    static startCustomMetadataVector(builder, numElems) {
      builder.startVector(4, numElems, 4);
    }
    static endMessage(builder) {
      const offset = builder.endObject();
      return offset;
    }
    static finishMessageBuffer(builder, offset) {
      builder.finish(offset);
    }
    static finishSizePrefixedMessageBuffer(builder, offset) {
      builder.finish(offset, void 0, true);
    }
    static createMessage(builder, version, headerType, headerOffset, bodyLength, customMetadataOffset) {
      _Message.startMessage(builder);
      _Message.addVersion(builder, version);
      _Message.addHeaderType(builder, headerType);
      _Message.addHeader(builder, headerOffset);
      _Message.addBodyLength(builder, bodyLength);
      _Message.addCustomMetadata(builder, customMetadataOffset);
      return _Message.endMessage(builder);
    }
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/typeassembler.mjs
  var Long3 = Long;
  var TypeAssembler = class extends Visitor {
    visit(node, builder) {
      return node == null || builder == null ? void 0 : super.visit(node, builder);
    }
    visitNull(_node, b) {
      Null2.startNull(b);
      return Null2.endNull(b);
    }
    visitInt(node, b) {
      Int.startInt(b);
      Int.addBitWidth(b, node.bitWidth);
      Int.addIsSigned(b, node.isSigned);
      return Int.endInt(b);
    }
    visitFloat(node, b) {
      FloatingPoint.startFloatingPoint(b);
      FloatingPoint.addPrecision(b, node.precision);
      return FloatingPoint.endFloatingPoint(b);
    }
    visitBinary(_node, b) {
      Binary2.startBinary(b);
      return Binary2.endBinary(b);
    }
    visitBool(_node, b) {
      Bool2.startBool(b);
      return Bool2.endBool(b);
    }
    visitUtf8(_node, b) {
      Utf82.startUtf8(b);
      return Utf82.endUtf8(b);
    }
    visitDecimal(node, b) {
      Decimal2.startDecimal(b);
      Decimal2.addScale(b, node.scale);
      Decimal2.addPrecision(b, node.precision);
      Decimal2.addBitWidth(b, node.bitWidth);
      return Decimal2.endDecimal(b);
    }
    visitDate(node, b) {
      Date2.startDate(b);
      Date2.addUnit(b, node.unit);
      return Date2.endDate(b);
    }
    visitTime(node, b) {
      Time.startTime(b);
      Time.addUnit(b, node.unit);
      Time.addBitWidth(b, node.bitWidth);
      return Time.endTime(b);
    }
    visitTimestamp(node, b) {
      const timezone = node.timezone && b.createString(node.timezone) || void 0;
      Timestamp.startTimestamp(b);
      Timestamp.addUnit(b, node.unit);
      if (timezone !== void 0) {
        Timestamp.addTimezone(b, timezone);
      }
      return Timestamp.endTimestamp(b);
    }
    visitInterval(node, b) {
      Interval.startInterval(b);
      Interval.addUnit(b, node.unit);
      return Interval.endInterval(b);
    }
    visitList(_node, b) {
      List2.startList(b);
      return List2.endList(b);
    }
    visitStruct(_node, b) {
      Struct_.startStruct_(b);
      return Struct_.endStruct_(b);
    }
    visitUnion(node, b) {
      Union.startTypeIdsVector(b, node.typeIds.length);
      const typeIds = Union.createTypeIdsVector(b, node.typeIds);
      Union.startUnion(b);
      Union.addMode(b, node.mode);
      Union.addTypeIds(b, typeIds);
      return Union.endUnion(b);
    }
    visitDictionary(node, b) {
      const indexType = this.visit(node.indices, b);
      DictionaryEncoding.startDictionaryEncoding(b);
      DictionaryEncoding.addId(b, new Long3(node.id, 0));
      DictionaryEncoding.addIsOrdered(b, node.isOrdered);
      if (indexType !== void 0) {
        DictionaryEncoding.addIndexType(b, indexType);
      }
      return DictionaryEncoding.endDictionaryEncoding(b);
    }
    visitFixedSizeBinary(node, b) {
      FixedSizeBinary2.startFixedSizeBinary(b);
      FixedSizeBinary2.addByteWidth(b, node.byteWidth);
      return FixedSizeBinary2.endFixedSizeBinary(b);
    }
    visitFixedSizeList(node, b) {
      FixedSizeList2.startFixedSizeList(b);
      FixedSizeList2.addListSize(b, node.listSize);
      return FixedSizeList2.endFixedSizeList(b);
    }
    visitMap(node, b) {
      Map2.startMap(b);
      Map2.addKeysSorted(b, node.keysSorted);
      return Map2.endMap(b);
    }
  };
  var instance8 = new TypeAssembler();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/metadata/json.mjs
  function schemaFromJSON(_schema, dictionaries = /* @__PURE__ */ new Map()) {
    return new Schema2(schemaFieldsFromJSON(_schema, dictionaries), customMetadataFromJSON(_schema["customMetadata"]), dictionaries);
  }
  function recordBatchFromJSON(b) {
    return new RecordBatch3(b["count"], fieldNodesFromJSON(b["columns"]), buffersFromJSON(b["columns"]));
  }
  function dictionaryBatchFromJSON(b) {
    return new DictionaryBatch2(recordBatchFromJSON(b["data"]), b["id"], b["isDelta"]);
  }
  function schemaFieldsFromJSON(_schema, dictionaries) {
    return (_schema["fields"] || []).filter(Boolean).map((f) => Field2.fromJSON(f, dictionaries));
  }
  function fieldChildrenFromJSON(_field, dictionaries) {
    return (_field["children"] || []).filter(Boolean).map((f) => Field2.fromJSON(f, dictionaries));
  }
  function fieldNodesFromJSON(xs) {
    return (xs || []).reduce((fieldNodes, column) => [
      ...fieldNodes,
      new FieldNode2(column["count"], nullCountFromJSON(column["VALIDITY"])),
      ...fieldNodesFromJSON(column["children"])
    ], []);
  }
  function buffersFromJSON(xs, buffers = []) {
    for (let i = -1, n = (xs || []).length; ++i < n; ) {
      const column = xs[i];
      column["VALIDITY"] && buffers.push(new BufferRegion(buffers.length, column["VALIDITY"].length));
      column["TYPE"] && buffers.push(new BufferRegion(buffers.length, column["TYPE"].length));
      column["OFFSET"] && buffers.push(new BufferRegion(buffers.length, column["OFFSET"].length));
      column["DATA"] && buffers.push(new BufferRegion(buffers.length, column["DATA"].length));
      buffers = buffersFromJSON(column["children"], buffers);
    }
    return buffers;
  }
  function nullCountFromJSON(validity) {
    return (validity || []).reduce((sum2, val) => sum2 + +(val === 0), 0);
  }
  function fieldFromJSON(_field, dictionaries) {
    let id;
    let keys;
    let field;
    let dictMeta;
    let type2;
    let dictType;
    if (!dictionaries || !(dictMeta = _field["dictionary"])) {
      type2 = typeFromJSON(_field, fieldChildrenFromJSON(_field, dictionaries));
      field = new Field2(_field["name"], type2, _field["nullable"], customMetadataFromJSON(_field["customMetadata"]));
    } else if (!dictionaries.has(id = dictMeta["id"])) {
      keys = (keys = dictMeta["indexType"]) ? indexTypeFromJSON(keys) : new Int32();
      dictionaries.set(id, type2 = typeFromJSON(_field, fieldChildrenFromJSON(_field, dictionaries)));
      dictType = new Dictionary(type2, keys, id, dictMeta["isOrdered"]);
      field = new Field2(_field["name"], dictType, _field["nullable"], customMetadataFromJSON(_field["customMetadata"]));
    } else {
      keys = (keys = dictMeta["indexType"]) ? indexTypeFromJSON(keys) : new Int32();
      dictType = new Dictionary(dictionaries.get(id), keys, id, dictMeta["isOrdered"]);
      field = new Field2(_field["name"], dictType, _field["nullable"], customMetadataFromJSON(_field["customMetadata"]));
    }
    return field || null;
  }
  function customMetadataFromJSON(_metadata) {
    return new Map(Object.entries(_metadata || {}));
  }
  function indexTypeFromJSON(_type) {
    return new Int_(_type["isSigned"], _type["bitWidth"]);
  }
  function typeFromJSON(f, children) {
    const typeId = f["type"]["name"];
    switch (typeId) {
      case "NONE":
        return new Null();
      case "null":
        return new Null();
      case "binary":
        return new Binary();
      case "utf8":
        return new Utf8();
      case "bool":
        return new Bool();
      case "list":
        return new List((children || [])[0]);
      case "struct":
        return new Struct(children || []);
      case "struct_":
        return new Struct(children || []);
    }
    switch (typeId) {
      case "int": {
        const t = f["type"];
        return new Int_(t["isSigned"], t["bitWidth"]);
      }
      case "floatingpoint": {
        const t = f["type"];
        return new Float(Precision[t["precision"]]);
      }
      case "decimal": {
        const t = f["type"];
        return new Decimal(t["scale"], t["precision"], t["bitWidth"]);
      }
      case "date": {
        const t = f["type"];
        return new Date_(DateUnit[t["unit"]]);
      }
      case "time": {
        const t = f["type"];
        return new Time_(TimeUnit[t["unit"]], t["bitWidth"]);
      }
      case "timestamp": {
        const t = f["type"];
        return new Timestamp_(TimeUnit[t["unit"]], t["timezone"]);
      }
      case "interval": {
        const t = f["type"];
        return new Interval_(IntervalUnit[t["unit"]]);
      }
      case "union": {
        const t = f["type"];
        return new Union_(UnionMode[t["mode"]], t["typeIds"] || [], children || []);
      }
      case "fixedsizebinary": {
        const t = f["type"];
        return new FixedSizeBinary(t["byteWidth"]);
      }
      case "fixedsizelist": {
        const t = f["type"];
        return new FixedSizeList(t["listSize"], (children || [])[0]);
      }
      case "map": {
        const t = f["type"];
        return new Map_((children || [])[0], t["keysSorted"]);
      }
    }
    throw new Error(`Unrecognized type: "${typeId}"`);
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/metadata/message.mjs
  var Long4 = Long;
  var Builder4 = Builder2;
  var ByteBuffer3 = ByteBuffer;
  var Message2 = class _Message {
    constructor(bodyLength, version, headerType, header) {
      this._version = version;
      this._headerType = headerType;
      this.body = new Uint8Array(0);
      header && (this._createHeader = () => header);
      this._bodyLength = typeof bodyLength === "number" ? bodyLength : bodyLength.low;
    }
    /** @nocollapse */
    static fromJSON(msg, headerType) {
      const message = new _Message(0, MetadataVersion.V4, headerType);
      message._createHeader = messageHeaderFromJSON(msg, headerType);
      return message;
    }
    /** @nocollapse */
    static decode(buf) {
      buf = new ByteBuffer3(toUint8Array(buf));
      const _message = Message.getRootAsMessage(buf);
      const bodyLength = _message.bodyLength();
      const version = _message.version();
      const headerType = _message.headerType();
      const message = new _Message(bodyLength, version, headerType);
      message._createHeader = decodeMessageHeader(_message, headerType);
      return message;
    }
    /** @nocollapse */
    static encode(message) {
      const b = new Builder4();
      let headerOffset = -1;
      if (message.isSchema()) {
        headerOffset = Schema2.encode(b, message.header());
      } else if (message.isRecordBatch()) {
        headerOffset = RecordBatch3.encode(b, message.header());
      } else if (message.isDictionaryBatch()) {
        headerOffset = DictionaryBatch2.encode(b, message.header());
      }
      Message.startMessage(b);
      Message.addVersion(b, MetadataVersion.V4);
      Message.addHeader(b, headerOffset);
      Message.addHeaderType(b, message.headerType);
      Message.addBodyLength(b, new Long4(message.bodyLength, 0));
      Message.finishMessageBuffer(b, Message.endMessage(b));
      return b.asUint8Array();
    }
    /** @nocollapse */
    static from(header, bodyLength = 0) {
      if (header instanceof Schema2) {
        return new _Message(0, MetadataVersion.V4, MessageHeader.Schema, header);
      }
      if (header instanceof RecordBatch3) {
        return new _Message(bodyLength, MetadataVersion.V4, MessageHeader.RecordBatch, header);
      }
      if (header instanceof DictionaryBatch2) {
        return new _Message(bodyLength, MetadataVersion.V4, MessageHeader.DictionaryBatch, header);
      }
      throw new Error(`Unrecognized Message header: ${header}`);
    }
    get type() {
      return this.headerType;
    }
    get version() {
      return this._version;
    }
    get headerType() {
      return this._headerType;
    }
    get bodyLength() {
      return this._bodyLength;
    }
    header() {
      return this._createHeader();
    }
    isSchema() {
      return this.headerType === MessageHeader.Schema;
    }
    isRecordBatch() {
      return this.headerType === MessageHeader.RecordBatch;
    }
    isDictionaryBatch() {
      return this.headerType === MessageHeader.DictionaryBatch;
    }
  };
  var RecordBatch3 = class {
    constructor(length, nodes, buffers) {
      this._nodes = nodes;
      this._buffers = buffers;
      this._length = typeof length === "number" ? length : length.low;
    }
    get nodes() {
      return this._nodes;
    }
    get length() {
      return this._length;
    }
    get buffers() {
      return this._buffers;
    }
  };
  var DictionaryBatch2 = class {
    constructor(data, id, isDelta = false) {
      this._data = data;
      this._isDelta = isDelta;
      this._id = typeof id === "number" ? id : id.low;
    }
    get id() {
      return this._id;
    }
    get data() {
      return this._data;
    }
    get isDelta() {
      return this._isDelta;
    }
    get length() {
      return this.data.length;
    }
    get nodes() {
      return this.data.nodes;
    }
    get buffers() {
      return this.data.buffers;
    }
  };
  var BufferRegion = class {
    constructor(offset, length) {
      this.offset = typeof offset === "number" ? offset : offset.low;
      this.length = typeof length === "number" ? length : length.low;
    }
  };
  var FieldNode2 = class {
    constructor(length, nullCount) {
      this.length = typeof length === "number" ? length : length.low;
      this.nullCount = typeof nullCount === "number" ? nullCount : nullCount.low;
    }
  };
  function messageHeaderFromJSON(message, type2) {
    return () => {
      switch (type2) {
        case MessageHeader.Schema:
          return Schema2.fromJSON(message);
        case MessageHeader.RecordBatch:
          return RecordBatch3.fromJSON(message);
        case MessageHeader.DictionaryBatch:
          return DictionaryBatch2.fromJSON(message);
      }
      throw new Error(`Unrecognized Message type: { name: ${MessageHeader[type2]}, type: ${type2} }`);
    };
  }
  function decodeMessageHeader(message, type2) {
    return () => {
      switch (type2) {
        case MessageHeader.Schema:
          return Schema2.decode(message.header(new Schema()));
        case MessageHeader.RecordBatch:
          return RecordBatch3.decode(message.header(new RecordBatch2()), message.version());
        case MessageHeader.DictionaryBatch:
          return DictionaryBatch2.decode(message.header(new DictionaryBatch()), message.version());
      }
      throw new Error(`Unrecognized Message type: { name: ${MessageHeader[type2]}, type: ${type2} }`);
    };
  }
  Field2["encode"] = encodeField;
  Field2["decode"] = decodeField;
  Field2["fromJSON"] = fieldFromJSON;
  Schema2["encode"] = encodeSchema;
  Schema2["decode"] = decodeSchema;
  Schema2["fromJSON"] = schemaFromJSON;
  RecordBatch3["encode"] = encodeRecordBatch;
  RecordBatch3["decode"] = decodeRecordBatch;
  RecordBatch3["fromJSON"] = recordBatchFromJSON;
  DictionaryBatch2["encode"] = encodeDictionaryBatch;
  DictionaryBatch2["decode"] = decodeDictionaryBatch;
  DictionaryBatch2["fromJSON"] = dictionaryBatchFromJSON;
  FieldNode2["encode"] = encodeFieldNode;
  FieldNode2["decode"] = decodeFieldNode;
  BufferRegion["encode"] = encodeBufferRegion;
  BufferRegion["decode"] = decodeBufferRegion;
  function decodeSchema(_schema, dictionaries = /* @__PURE__ */ new Map()) {
    const fields = decodeSchemaFields(_schema, dictionaries);
    return new Schema2(fields, decodeCustomMetadata(_schema), dictionaries);
  }
  function decodeRecordBatch(batch, version = MetadataVersion.V4) {
    if (batch.compression() !== null) {
      throw new Error("Record batch compression not implemented");
    }
    return new RecordBatch3(batch.length(), decodeFieldNodes(batch), decodeBuffers(batch, version));
  }
  function decodeDictionaryBatch(batch, version = MetadataVersion.V4) {
    return new DictionaryBatch2(RecordBatch3.decode(batch.data(), version), batch.id(), batch.isDelta());
  }
  function decodeBufferRegion(b) {
    return new BufferRegion(b.offset(), b.length());
  }
  function decodeFieldNode(f) {
    return new FieldNode2(f.length(), f.nullCount());
  }
  function decodeFieldNodes(batch) {
    const nodes = [];
    for (let f, i = -1, j = -1, n = batch.nodesLength(); ++i < n; ) {
      if (f = batch.nodes(i)) {
        nodes[++j] = FieldNode2.decode(f);
      }
    }
    return nodes;
  }
  function decodeBuffers(batch, version) {
    const bufferRegions = [];
    for (let b, i = -1, j = -1, n = batch.buffersLength(); ++i < n; ) {
      if (b = batch.buffers(i)) {
        if (version < MetadataVersion.V4) {
          b.bb_pos += 8 * (i + 1);
        }
        bufferRegions[++j] = BufferRegion.decode(b);
      }
    }
    return bufferRegions;
  }
  function decodeSchemaFields(schema, dictionaries) {
    const fields = [];
    for (let f, i = -1, j = -1, n = schema.fieldsLength(); ++i < n; ) {
      if (f = schema.fields(i)) {
        fields[++j] = Field2.decode(f, dictionaries);
      }
    }
    return fields;
  }
  function decodeFieldChildren(field, dictionaries) {
    const children = [];
    for (let f, i = -1, j = -1, n = field.childrenLength(); ++i < n; ) {
      if (f = field.children(i)) {
        children[++j] = Field2.decode(f, dictionaries);
      }
    }
    return children;
  }
  function decodeField(f, dictionaries) {
    let id;
    let field;
    let type2;
    let keys;
    let dictType;
    let dictMeta;
    if (!dictionaries || !(dictMeta = f.dictionary())) {
      type2 = decodeFieldType(f, decodeFieldChildren(f, dictionaries));
      field = new Field2(f.name(), type2, f.nullable(), decodeCustomMetadata(f));
    } else if (!dictionaries.has(id = dictMeta.id().low)) {
      keys = (keys = dictMeta.indexType()) ? decodeIndexType(keys) : new Int32();
      dictionaries.set(id, type2 = decodeFieldType(f, decodeFieldChildren(f, dictionaries)));
      dictType = new Dictionary(type2, keys, id, dictMeta.isOrdered());
      field = new Field2(f.name(), dictType, f.nullable(), decodeCustomMetadata(f));
    } else {
      keys = (keys = dictMeta.indexType()) ? decodeIndexType(keys) : new Int32();
      dictType = new Dictionary(dictionaries.get(id), keys, id, dictMeta.isOrdered());
      field = new Field2(f.name(), dictType, f.nullable(), decodeCustomMetadata(f));
    }
    return field || null;
  }
  function decodeCustomMetadata(parent) {
    const data = /* @__PURE__ */ new Map();
    if (parent) {
      for (let entry, key, i = -1, n = Math.trunc(parent.customMetadataLength()); ++i < n; ) {
        if ((entry = parent.customMetadata(i)) && (key = entry.key()) != null) {
          data.set(key, entry.value());
        }
      }
    }
    return data;
  }
  function decodeIndexType(_type) {
    return new Int_(_type.isSigned(), _type.bitWidth());
  }
  function decodeFieldType(f, children) {
    const typeId = f.typeType();
    switch (typeId) {
      case Type2["NONE"]:
        return new Null();
      case Type2["Null"]:
        return new Null();
      case Type2["Binary"]:
        return new Binary();
      case Type2["Utf8"]:
        return new Utf8();
      case Type2["Bool"]:
        return new Bool();
      case Type2["List"]:
        return new List((children || [])[0]);
      case Type2["Struct_"]:
        return new Struct(children || []);
    }
    switch (typeId) {
      case Type2["Int"]: {
        const t = f.type(new Int());
        return new Int_(t.isSigned(), t.bitWidth());
      }
      case Type2["FloatingPoint"]: {
        const t = f.type(new FloatingPoint());
        return new Float(t.precision());
      }
      case Type2["Decimal"]: {
        const t = f.type(new Decimal2());
        return new Decimal(t.scale(), t.precision(), t.bitWidth());
      }
      case Type2["Date"]: {
        const t = f.type(new Date2());
        return new Date_(t.unit());
      }
      case Type2["Time"]: {
        const t = f.type(new Time());
        return new Time_(t.unit(), t.bitWidth());
      }
      case Type2["Timestamp"]: {
        const t = f.type(new Timestamp());
        return new Timestamp_(t.unit(), t.timezone());
      }
      case Type2["Interval"]: {
        const t = f.type(new Interval());
        return new Interval_(t.unit());
      }
      case Type2["Union"]: {
        const t = f.type(new Union());
        return new Union_(t.mode(), t.typeIdsArray() || [], children || []);
      }
      case Type2["FixedSizeBinary"]: {
        const t = f.type(new FixedSizeBinary2());
        return new FixedSizeBinary(t.byteWidth());
      }
      case Type2["FixedSizeList"]: {
        const t = f.type(new FixedSizeList2());
        return new FixedSizeList(t.listSize(), (children || [])[0]);
      }
      case Type2["Map"]: {
        const t = f.type(new Map2());
        return new Map_((children || [])[0], t.keysSorted());
      }
    }
    throw new Error(`Unrecognized type: "${Type2[typeId]}" (${typeId})`);
  }
  function encodeSchema(b, schema) {
    const fieldOffsets = schema.fields.map((f) => Field2.encode(b, f));
    Schema.startFieldsVector(b, fieldOffsets.length);
    const fieldsVectorOffset = Schema.createFieldsVector(b, fieldOffsets);
    const metadataOffset = !(schema.metadata && schema.metadata.size > 0) ? -1 : Schema.createCustomMetadataVector(b, [...schema.metadata].map(([k, v]) => {
      const key = b.createString(`${k}`);
      const val = b.createString(`${v}`);
      KeyValue.startKeyValue(b);
      KeyValue.addKey(b, key);
      KeyValue.addValue(b, val);
      return KeyValue.endKeyValue(b);
    }));
    Schema.startSchema(b);
    Schema.addFields(b, fieldsVectorOffset);
    Schema.addEndianness(b, platformIsLittleEndian ? Endianness.Little : Endianness.Big);
    if (metadataOffset !== -1) {
      Schema.addCustomMetadata(b, metadataOffset);
    }
    return Schema.endSchema(b);
  }
  function encodeField(b, field) {
    let nameOffset = -1;
    let typeOffset = -1;
    let dictionaryOffset = -1;
    const type2 = field.type;
    let typeId = field.typeId;
    if (!DataType.isDictionary(type2)) {
      typeOffset = instance8.visit(type2, b);
    } else {
      typeId = type2.dictionary.typeId;
      dictionaryOffset = instance8.visit(type2, b);
      typeOffset = instance8.visit(type2.dictionary, b);
    }
    const childOffsets = (type2.children || []).map((f) => Field2.encode(b, f));
    const childrenVectorOffset = Field.createChildrenVector(b, childOffsets);
    const metadataOffset = !(field.metadata && field.metadata.size > 0) ? -1 : Field.createCustomMetadataVector(b, [...field.metadata].map(([k, v]) => {
      const key = b.createString(`${k}`);
      const val = b.createString(`${v}`);
      KeyValue.startKeyValue(b);
      KeyValue.addKey(b, key);
      KeyValue.addValue(b, val);
      return KeyValue.endKeyValue(b);
    }));
    if (field.name) {
      nameOffset = b.createString(field.name);
    }
    Field.startField(b);
    Field.addType(b, typeOffset);
    Field.addTypeType(b, typeId);
    Field.addChildren(b, childrenVectorOffset);
    Field.addNullable(b, !!field.nullable);
    if (nameOffset !== -1) {
      Field.addName(b, nameOffset);
    }
    if (dictionaryOffset !== -1) {
      Field.addDictionary(b, dictionaryOffset);
    }
    if (metadataOffset !== -1) {
      Field.addCustomMetadata(b, metadataOffset);
    }
    return Field.endField(b);
  }
  function encodeRecordBatch(b, recordBatch) {
    const nodes = recordBatch.nodes || [];
    const buffers = recordBatch.buffers || [];
    RecordBatch2.startNodesVector(b, nodes.length);
    for (const n of nodes.slice().reverse())
      FieldNode2.encode(b, n);
    const nodesVectorOffset = b.endVector();
    RecordBatch2.startBuffersVector(b, buffers.length);
    for (const b_ of buffers.slice().reverse())
      BufferRegion.encode(b, b_);
    const buffersVectorOffset = b.endVector();
    RecordBatch2.startRecordBatch(b);
    RecordBatch2.addLength(b, new Long4(recordBatch.length, 0));
    RecordBatch2.addNodes(b, nodesVectorOffset);
    RecordBatch2.addBuffers(b, buffersVectorOffset);
    return RecordBatch2.endRecordBatch(b);
  }
  function encodeDictionaryBatch(b, dictionaryBatch) {
    const dataOffset = RecordBatch3.encode(b, dictionaryBatch.data);
    DictionaryBatch.startDictionaryBatch(b);
    DictionaryBatch.addId(b, new Long4(dictionaryBatch.id, 0));
    DictionaryBatch.addIsDelta(b, dictionaryBatch.isDelta);
    DictionaryBatch.addData(b, dataOffset);
    return DictionaryBatch.endDictionaryBatch(b);
  }
  function encodeFieldNode(b, node) {
    return FieldNode.createFieldNode(b, new Long4(node.length, 0), new Long4(node.nullCount, 0));
  }
  function encodeBufferRegion(b, node) {
    return Buffer2.createBuffer(b, new Long4(node.offset, 0), new Long4(node.length, 0));
  }
  var platformIsLittleEndian = (() => {
    const buffer = new ArrayBuffer(2);
    new DataView(buffer).setInt16(
      0,
      256,
      true
      /* littleEndian */
    );
    return new Int16Array(buffer)[0] === 256;
  })();

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/message.mjs
  var invalidMessageType = (type2) => `Expected ${MessageHeader[type2]} Message in stream, but was null or length 0.`;
  var nullMessage = (type2) => `Header pointer of flatbuffer-encoded ${MessageHeader[type2]} Message is null or length 0.`;
  var invalidMessageMetadata = (expected, actual) => `Expected to read ${expected} metadata bytes, but only read ${actual}.`;
  var invalidMessageBodyLength = (expected, actual) => `Expected to read ${expected} bytes for message body, but only read ${actual}.`;
  var MessageReader = class {
    constructor(source) {
      this.source = source instanceof ByteStream ? source : new ByteStream(source);
    }
    [Symbol.iterator]() {
      return this;
    }
    next() {
      let r;
      if ((r = this.readMetadataLength()).done) {
        return ITERATOR_DONE;
      }
      if (r.value === -1 && (r = this.readMetadataLength()).done) {
        return ITERATOR_DONE;
      }
      if ((r = this.readMetadata(r.value)).done) {
        return ITERATOR_DONE;
      }
      return r;
    }
    throw(value) {
      return this.source.throw(value);
    }
    return(value) {
      return this.source.return(value);
    }
    readMessage(type2) {
      let r;
      if ((r = this.next()).done) {
        return null;
      }
      if (type2 != null && r.value.headerType !== type2) {
        throw new Error(invalidMessageType(type2));
      }
      return r.value;
    }
    readMessageBody(bodyLength) {
      if (bodyLength <= 0) {
        return new Uint8Array(0);
      }
      const buf = toUint8Array(this.source.read(bodyLength));
      if (buf.byteLength < bodyLength) {
        throw new Error(invalidMessageBodyLength(bodyLength, buf.byteLength));
      }
      return (
        /* 1. */
        buf.byteOffset % 8 === 0 && /* 2. */
        buf.byteOffset + buf.byteLength <= buf.buffer.byteLength ? buf : buf.slice()
      );
    }
    readSchema(throwIfNull = false) {
      const type2 = MessageHeader.Schema;
      const message = this.readMessage(type2);
      const schema = message === null || message === void 0 ? void 0 : message.header();
      if (throwIfNull && !schema) {
        throw new Error(nullMessage(type2));
      }
      return schema;
    }
    readMetadataLength() {
      const buf = this.source.read(PADDING);
      const bb = buf && new ByteBuffer(buf);
      const len = (bb === null || bb === void 0 ? void 0 : bb.readInt32(0)) || 0;
      return { done: len === 0, value: len };
    }
    readMetadata(metadataLength) {
      const buf = this.source.read(metadataLength);
      if (!buf) {
        return ITERATOR_DONE;
      }
      if (buf.byteLength < metadataLength) {
        throw new Error(invalidMessageMetadata(metadataLength, buf.byteLength));
      }
      return { done: false, value: Message2.decode(buf) };
    }
  };
  var AsyncMessageReader = class {
    constructor(source, byteLength) {
      this.source = source instanceof AsyncByteStream ? source : isFileHandle(source) ? new AsyncRandomAccessFile(source, byteLength) : new AsyncByteStream(source);
    }
    [Symbol.asyncIterator]() {
      return this;
    }
    next() {
      return __awaiter(this, void 0, void 0, function* () {
        let r;
        if ((r = yield this.readMetadataLength()).done) {
          return ITERATOR_DONE;
        }
        if (r.value === -1 && (r = yield this.readMetadataLength()).done) {
          return ITERATOR_DONE;
        }
        if ((r = yield this.readMetadata(r.value)).done) {
          return ITERATOR_DONE;
        }
        return r;
      });
    }
    throw(value) {
      return __awaiter(this, void 0, void 0, function* () {
        return yield this.source.throw(value);
      });
    }
    return(value) {
      return __awaiter(this, void 0, void 0, function* () {
        return yield this.source.return(value);
      });
    }
    readMessage(type2) {
      return __awaiter(this, void 0, void 0, function* () {
        let r;
        if ((r = yield this.next()).done) {
          return null;
        }
        if (type2 != null && r.value.headerType !== type2) {
          throw new Error(invalidMessageType(type2));
        }
        return r.value;
      });
    }
    readMessageBody(bodyLength) {
      return __awaiter(this, void 0, void 0, function* () {
        if (bodyLength <= 0) {
          return new Uint8Array(0);
        }
        const buf = toUint8Array(yield this.source.read(bodyLength));
        if (buf.byteLength < bodyLength) {
          throw new Error(invalidMessageBodyLength(bodyLength, buf.byteLength));
        }
        return (
          /* 1. */
          buf.byteOffset % 8 === 0 && /* 2. */
          buf.byteOffset + buf.byteLength <= buf.buffer.byteLength ? buf : buf.slice()
        );
      });
    }
    readSchema(throwIfNull = false) {
      return __awaiter(this, void 0, void 0, function* () {
        const type2 = MessageHeader.Schema;
        const message = yield this.readMessage(type2);
        const schema = message === null || message === void 0 ? void 0 : message.header();
        if (throwIfNull && !schema) {
          throw new Error(nullMessage(type2));
        }
        return schema;
      });
    }
    readMetadataLength() {
      return __awaiter(this, void 0, void 0, function* () {
        const buf = yield this.source.read(PADDING);
        const bb = buf && new ByteBuffer(buf);
        const len = (bb === null || bb === void 0 ? void 0 : bb.readInt32(0)) || 0;
        return { done: len === 0, value: len };
      });
    }
    readMetadata(metadataLength) {
      return __awaiter(this, void 0, void 0, function* () {
        const buf = yield this.source.read(metadataLength);
        if (!buf) {
          return ITERATOR_DONE;
        }
        if (buf.byteLength < metadataLength) {
          throw new Error(invalidMessageMetadata(metadataLength, buf.byteLength));
        }
        return { done: false, value: Message2.decode(buf) };
      });
    }
  };
  var JSONMessageReader = class extends MessageReader {
    constructor(source) {
      super(new Uint8Array(0));
      this._schema = false;
      this._body = [];
      this._batchIndex = 0;
      this._dictionaryIndex = 0;
      this._json = source instanceof ArrowJSON ? source : new ArrowJSON(source);
    }
    next() {
      const { _json } = this;
      if (!this._schema) {
        this._schema = true;
        const message = Message2.fromJSON(_json.schema, MessageHeader.Schema);
        return { done: false, value: message };
      }
      if (this._dictionaryIndex < _json.dictionaries.length) {
        const batch = _json.dictionaries[this._dictionaryIndex++];
        this._body = batch["data"]["columns"];
        const message = Message2.fromJSON(batch, MessageHeader.DictionaryBatch);
        return { done: false, value: message };
      }
      if (this._batchIndex < _json.batches.length) {
        const batch = _json.batches[this._batchIndex++];
        this._body = batch["columns"];
        const message = Message2.fromJSON(batch, MessageHeader.RecordBatch);
        return { done: false, value: message };
      }
      this._body = [];
      return ITERATOR_DONE;
    }
    readMessageBody(_bodyLength) {
      return flattenDataSources(this._body);
      function flattenDataSources(xs) {
        return (xs || []).reduce((buffers, column) => [
          ...buffers,
          ...column["VALIDITY"] && [column["VALIDITY"]] || [],
          ...column["TYPE"] && [column["TYPE"]] || [],
          ...column["OFFSET"] && [column["OFFSET"]] || [],
          ...column["DATA"] && [column["DATA"]] || [],
          ...flattenDataSources(column["children"])
        ], []);
      }
    }
    readMessage(type2) {
      let r;
      if ((r = this.next()).done) {
        return null;
      }
      if (type2 != null && r.value.headerType !== type2) {
        throw new Error(invalidMessageType(type2));
      }
      return r.value;
    }
    readSchema() {
      const type2 = MessageHeader.Schema;
      const message = this.readMessage(type2);
      const schema = message === null || message === void 0 ? void 0 : message.header();
      if (!message || !schema) {
        throw new Error(nullMessage(type2));
      }
      return schema;
    }
  };
  var PADDING = 4;
  var MAGIC_STR = "ARROW1";
  var MAGIC = new Uint8Array(MAGIC_STR.length);
  for (let i = 0; i < MAGIC_STR.length; i += 1) {
    MAGIC[i] = MAGIC_STR.codePointAt(i);
  }
  function checkForMagicArrowString(buffer, index = 0) {
    for (let i = -1, n = MAGIC.length; ++i < n; ) {
      if (MAGIC[i] !== buffer[index + i]) {
        return false;
      }
    }
    return true;
  }
  var magicLength = MAGIC.length;
  var magicAndPadding = magicLength + PADDING;
  var magicX2AndPadding = magicLength * 2 + PADDING;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/reader.mjs
  var RecordBatchReader = class _RecordBatchReader extends ReadableInterop {
    constructor(impl) {
      super();
      this._impl = impl;
    }
    get closed() {
      return this._impl.closed;
    }
    get schema() {
      return this._impl.schema;
    }
    get autoDestroy() {
      return this._impl.autoDestroy;
    }
    get dictionaries() {
      return this._impl.dictionaries;
    }
    get numDictionaries() {
      return this._impl.numDictionaries;
    }
    get numRecordBatches() {
      return this._impl.numRecordBatches;
    }
    get footer() {
      return this._impl.isFile() ? this._impl.footer : null;
    }
    isSync() {
      return this._impl.isSync();
    }
    isAsync() {
      return this._impl.isAsync();
    }
    isFile() {
      return this._impl.isFile();
    }
    isStream() {
      return this._impl.isStream();
    }
    next() {
      return this._impl.next();
    }
    throw(value) {
      return this._impl.throw(value);
    }
    return(value) {
      return this._impl.return(value);
    }
    cancel() {
      return this._impl.cancel();
    }
    reset(schema) {
      this._impl.reset(schema);
      this._DOMStream = void 0;
      this._nodeStream = void 0;
      return this;
    }
    open(options) {
      const opening = this._impl.open(options);
      return isPromise(opening) ? opening.then(() => this) : this;
    }
    readRecordBatch(index) {
      return this._impl.isFile() ? this._impl.readRecordBatch(index) : null;
    }
    [Symbol.iterator]() {
      return this._impl[Symbol.iterator]();
    }
    [Symbol.asyncIterator]() {
      return this._impl[Symbol.asyncIterator]();
    }
    toDOMStream() {
      return adapters_default.toDOMStream(this.isSync() ? { [Symbol.iterator]: () => this } : { [Symbol.asyncIterator]: () => this });
    }
    toNodeStream() {
      return adapters_default.toNodeStream(this.isSync() ? { [Symbol.iterator]: () => this } : { [Symbol.asyncIterator]: () => this }, { objectMode: true });
    }
    /** @nocollapse */
    // @ts-ignore
    static throughNode(options) {
      throw new Error(`"throughNode" not available in this environment`);
    }
    /** @nocollapse */
    static throughDOM(writableStrategy, readableStrategy) {
      throw new Error(`"throughDOM" not available in this environment`);
    }
    /** @nocollapse */
    static from(source) {
      if (source instanceof _RecordBatchReader) {
        return source;
      } else if (isArrowJSON(source)) {
        return fromArrowJSON(source);
      } else if (isFileHandle(source)) {
        return fromFileHandle(source);
      } else if (isPromise(source)) {
        return (() => __awaiter(this, void 0, void 0, function* () {
          return yield _RecordBatchReader.from(yield source);
        }))();
      } else if (isFetchResponse(source) || isReadableDOMStream(source) || isReadableNodeStream(source) || isAsyncIterable(source)) {
        return fromAsyncByteStream(new AsyncByteStream(source));
      }
      return fromByteStream(new ByteStream(source));
    }
    /** @nocollapse */
    static readAll(source) {
      if (source instanceof _RecordBatchReader) {
        return source.isSync() ? readAllSync(source) : readAllAsync(source);
      } else if (isArrowJSON(source) || ArrayBuffer.isView(source) || isIterable(source) || isIteratorResult(source)) {
        return readAllSync(source);
      }
      return readAllAsync(source);
    }
  };
  var RecordBatchStreamReader = class extends RecordBatchReader {
    constructor(_impl) {
      super(_impl);
      this._impl = _impl;
    }
    readAll() {
      return [...this];
    }
    [Symbol.iterator]() {
      return this._impl[Symbol.iterator]();
    }
    [Symbol.asyncIterator]() {
      return __asyncGenerator(this, arguments, function* _a5() {
        yield __await(yield* __asyncDelegator(__asyncValues(this[Symbol.iterator]())));
      });
    }
  };
  var AsyncRecordBatchStreamReader = class extends RecordBatchReader {
    constructor(_impl) {
      super(_impl);
      this._impl = _impl;
    }
    readAll() {
      var e_1, _a5;
      return __awaiter(this, void 0, void 0, function* () {
        const batches = new Array();
        try {
          for (var _b2 = __asyncValues(this), _c2; _c2 = yield _b2.next(), !_c2.done; ) {
            const batch = _c2.value;
            batches.push(batch);
          }
        } catch (e_1_1) {
          e_1 = { error: e_1_1 };
        } finally {
          try {
            if (_c2 && !_c2.done && (_a5 = _b2.return)) yield _a5.call(_b2);
          } finally {
            if (e_1) throw e_1.error;
          }
        }
        return batches;
      });
    }
    [Symbol.iterator]() {
      throw new Error(`AsyncRecordBatchStreamReader is not Iterable`);
    }
    [Symbol.asyncIterator]() {
      return this._impl[Symbol.asyncIterator]();
    }
  };
  var RecordBatchFileReader = class extends RecordBatchStreamReader {
    constructor(_impl) {
      super(_impl);
      this._impl = _impl;
    }
  };
  var AsyncRecordBatchFileReader = class extends AsyncRecordBatchStreamReader {
    constructor(_impl) {
      super(_impl);
      this._impl = _impl;
    }
  };
  var RecordBatchReaderImpl = class {
    constructor(dictionaries = /* @__PURE__ */ new Map()) {
      this.closed = false;
      this.autoDestroy = true;
      this._dictionaryIndex = 0;
      this._recordBatchIndex = 0;
      this.dictionaries = dictionaries;
    }
    get numDictionaries() {
      return this._dictionaryIndex;
    }
    get numRecordBatches() {
      return this._recordBatchIndex;
    }
    isSync() {
      return false;
    }
    isAsync() {
      return false;
    }
    isFile() {
      return false;
    }
    isStream() {
      return false;
    }
    reset(schema) {
      this._dictionaryIndex = 0;
      this._recordBatchIndex = 0;
      this.schema = schema;
      this.dictionaries = /* @__PURE__ */ new Map();
      return this;
    }
    _loadRecordBatch(header, body) {
      const children = this._loadVectors(header, body, this.schema.fields);
      const data = makeData({ type: new Struct(this.schema.fields), length: header.length, children });
      return new RecordBatch(this.schema, data);
    }
    _loadDictionaryBatch(header, body) {
      const { id, isDelta } = header;
      const { dictionaries, schema } = this;
      const dictionary = dictionaries.get(id);
      if (isDelta || !dictionary) {
        const type2 = schema.dictionaries.get(id);
        const data = this._loadVectors(header.data, body, [type2]);
        return (dictionary && isDelta ? dictionary.concat(new Vector(data)) : new Vector(data)).memoize();
      }
      return dictionary.memoize();
    }
    _loadVectors(header, body, types) {
      return new VectorLoader(body, header.nodes, header.buffers, this.dictionaries).visitMany(types);
    }
  };
  var RecordBatchStreamReaderImpl = class extends RecordBatchReaderImpl {
    constructor(source, dictionaries) {
      super(dictionaries);
      this._reader = !isArrowJSON(source) ? new MessageReader(this._handle = source) : new JSONMessageReader(this._handle = source);
    }
    isSync() {
      return true;
    }
    isStream() {
      return true;
    }
    [Symbol.iterator]() {
      return this;
    }
    cancel() {
      if (!this.closed && (this.closed = true)) {
        this.reset()._reader.return();
        this._reader = null;
        this.dictionaries = null;
      }
    }
    open(options) {
      if (!this.closed) {
        this.autoDestroy = shouldAutoDestroy(this, options);
        if (!(this.schema || (this.schema = this._reader.readSchema()))) {
          this.cancel();
        }
      }
      return this;
    }
    throw(value) {
      if (!this.closed && this.autoDestroy && (this.closed = true)) {
        return this.reset()._reader.throw(value);
      }
      return ITERATOR_DONE;
    }
    return(value) {
      if (!this.closed && this.autoDestroy && (this.closed = true)) {
        return this.reset()._reader.return(value);
      }
      return ITERATOR_DONE;
    }
    next() {
      if (this.closed) {
        return ITERATOR_DONE;
      }
      let message;
      const { _reader: reader } = this;
      while (message = this._readNextMessageAndValidate()) {
        if (message.isSchema()) {
          this.reset(message.header());
        } else if (message.isRecordBatch()) {
          this._recordBatchIndex++;
          const header = message.header();
          const buffer = reader.readMessageBody(message.bodyLength);
          const recordBatch = this._loadRecordBatch(header, buffer);
          return { done: false, value: recordBatch };
        } else if (message.isDictionaryBatch()) {
          this._dictionaryIndex++;
          const header = message.header();
          const buffer = reader.readMessageBody(message.bodyLength);
          const vector = this._loadDictionaryBatch(header, buffer);
          this.dictionaries.set(header.id, vector);
        }
      }
      if (this.schema && this._recordBatchIndex === 0) {
        this._recordBatchIndex++;
        return { done: false, value: new _InternalEmptyPlaceholderRecordBatch(this.schema) };
      }
      return this.return();
    }
    _readNextMessageAndValidate(type2) {
      return this._reader.readMessage(type2);
    }
  };
  var AsyncRecordBatchStreamReaderImpl = class extends RecordBatchReaderImpl {
    constructor(source, dictionaries) {
      super(dictionaries);
      this._reader = new AsyncMessageReader(this._handle = source);
    }
    isAsync() {
      return true;
    }
    isStream() {
      return true;
    }
    [Symbol.asyncIterator]() {
      return this;
    }
    cancel() {
      return __awaiter(this, void 0, void 0, function* () {
        if (!this.closed && (this.closed = true)) {
          yield this.reset()._reader.return();
          this._reader = null;
          this.dictionaries = null;
        }
      });
    }
    open(options) {
      return __awaiter(this, void 0, void 0, function* () {
        if (!this.closed) {
          this.autoDestroy = shouldAutoDestroy(this, options);
          if (!(this.schema || (this.schema = yield this._reader.readSchema()))) {
            yield this.cancel();
          }
        }
        return this;
      });
    }
    throw(value) {
      return __awaiter(this, void 0, void 0, function* () {
        if (!this.closed && this.autoDestroy && (this.closed = true)) {
          return yield this.reset()._reader.throw(value);
        }
        return ITERATOR_DONE;
      });
    }
    return(value) {
      return __awaiter(this, void 0, void 0, function* () {
        if (!this.closed && this.autoDestroy && (this.closed = true)) {
          return yield this.reset()._reader.return(value);
        }
        return ITERATOR_DONE;
      });
    }
    next() {
      return __awaiter(this, void 0, void 0, function* () {
        if (this.closed) {
          return ITERATOR_DONE;
        }
        let message;
        const { _reader: reader } = this;
        while (message = yield this._readNextMessageAndValidate()) {
          if (message.isSchema()) {
            yield this.reset(message.header());
          } else if (message.isRecordBatch()) {
            this._recordBatchIndex++;
            const header = message.header();
            const buffer = yield reader.readMessageBody(message.bodyLength);
            const recordBatch = this._loadRecordBatch(header, buffer);
            return { done: false, value: recordBatch };
          } else if (message.isDictionaryBatch()) {
            this._dictionaryIndex++;
            const header = message.header();
            const buffer = yield reader.readMessageBody(message.bodyLength);
            const vector = this._loadDictionaryBatch(header, buffer);
            this.dictionaries.set(header.id, vector);
          }
        }
        if (this.schema && this._recordBatchIndex === 0) {
          this._recordBatchIndex++;
          return { done: false, value: new _InternalEmptyPlaceholderRecordBatch(this.schema) };
        }
        return yield this.return();
      });
    }
    _readNextMessageAndValidate(type2) {
      return __awaiter(this, void 0, void 0, function* () {
        return yield this._reader.readMessage(type2);
      });
    }
  };
  var RecordBatchFileReaderImpl = class extends RecordBatchStreamReaderImpl {
    constructor(source, dictionaries) {
      super(source instanceof RandomAccessFile ? source : new RandomAccessFile(source), dictionaries);
    }
    get footer() {
      return this._footer;
    }
    get numDictionaries() {
      return this._footer ? this._footer.numDictionaries : 0;
    }
    get numRecordBatches() {
      return this._footer ? this._footer.numRecordBatches : 0;
    }
    isSync() {
      return true;
    }
    isFile() {
      return true;
    }
    open(options) {
      if (!this.closed && !this._footer) {
        this.schema = (this._footer = this._readFooter()).schema;
        for (const block of this._footer.dictionaryBatches()) {
          block && this._readDictionaryBatch(this._dictionaryIndex++);
        }
      }
      return super.open(options);
    }
    readRecordBatch(index) {
      var _a5;
      if (this.closed) {
        return null;
      }
      if (!this._footer) {
        this.open();
      }
      const block = (_a5 = this._footer) === null || _a5 === void 0 ? void 0 : _a5.getRecordBatch(index);
      if (block && this._handle.seek(block.offset)) {
        const message = this._reader.readMessage(MessageHeader.RecordBatch);
        if (message === null || message === void 0 ? void 0 : message.isRecordBatch()) {
          const header = message.header();
          const buffer = this._reader.readMessageBody(message.bodyLength);
          const recordBatch = this._loadRecordBatch(header, buffer);
          return recordBatch;
        }
      }
      return null;
    }
    _readDictionaryBatch(index) {
      var _a5;
      const block = (_a5 = this._footer) === null || _a5 === void 0 ? void 0 : _a5.getDictionaryBatch(index);
      if (block && this._handle.seek(block.offset)) {
        const message = this._reader.readMessage(MessageHeader.DictionaryBatch);
        if (message === null || message === void 0 ? void 0 : message.isDictionaryBatch()) {
          const header = message.header();
          const buffer = this._reader.readMessageBody(message.bodyLength);
          const vector = this._loadDictionaryBatch(header, buffer);
          this.dictionaries.set(header.id, vector);
        }
      }
    }
    _readFooter() {
      const { _handle } = this;
      const offset = _handle.size - magicAndPadding;
      const length = _handle.readInt32(offset);
      const buffer = _handle.readAt(offset - length, length);
      return Footer_.decode(buffer);
    }
    _readNextMessageAndValidate(type2) {
      var _a5;
      if (!this._footer) {
        this.open();
      }
      if (this._footer && this._recordBatchIndex < this.numRecordBatches) {
        const block = (_a5 = this._footer) === null || _a5 === void 0 ? void 0 : _a5.getRecordBatch(this._recordBatchIndex);
        if (block && this._handle.seek(block.offset)) {
          return this._reader.readMessage(type2);
        }
      }
      return null;
    }
  };
  var AsyncRecordBatchFileReaderImpl = class extends AsyncRecordBatchStreamReaderImpl {
    constructor(source, ...rest) {
      const byteLength = typeof rest[0] !== "number" ? rest.shift() : void 0;
      const dictionaries = rest[0] instanceof Map ? rest.shift() : void 0;
      super(source instanceof AsyncRandomAccessFile ? source : new AsyncRandomAccessFile(source, byteLength), dictionaries);
    }
    get footer() {
      return this._footer;
    }
    get numDictionaries() {
      return this._footer ? this._footer.numDictionaries : 0;
    }
    get numRecordBatches() {
      return this._footer ? this._footer.numRecordBatches : 0;
    }
    isFile() {
      return true;
    }
    isAsync() {
      return true;
    }
    open(options) {
      const _super = Object.create(null, {
        open: { get: () => super.open }
      });
      return __awaiter(this, void 0, void 0, function* () {
        if (!this.closed && !this._footer) {
          this.schema = (this._footer = yield this._readFooter()).schema;
          for (const block of this._footer.dictionaryBatches()) {
            block && (yield this._readDictionaryBatch(this._dictionaryIndex++));
          }
        }
        return yield _super.open.call(this, options);
      });
    }
    readRecordBatch(index) {
      var _a5;
      return __awaiter(this, void 0, void 0, function* () {
        if (this.closed) {
          return null;
        }
        if (!this._footer) {
          yield this.open();
        }
        const block = (_a5 = this._footer) === null || _a5 === void 0 ? void 0 : _a5.getRecordBatch(index);
        if (block && (yield this._handle.seek(block.offset))) {
          const message = yield this._reader.readMessage(MessageHeader.RecordBatch);
          if (message === null || message === void 0 ? void 0 : message.isRecordBatch()) {
            const header = message.header();
            const buffer = yield this._reader.readMessageBody(message.bodyLength);
            const recordBatch = this._loadRecordBatch(header, buffer);
            return recordBatch;
          }
        }
        return null;
      });
    }
    _readDictionaryBatch(index) {
      var _a5;
      return __awaiter(this, void 0, void 0, function* () {
        const block = (_a5 = this._footer) === null || _a5 === void 0 ? void 0 : _a5.getDictionaryBatch(index);
        if (block && (yield this._handle.seek(block.offset))) {
          const message = yield this._reader.readMessage(MessageHeader.DictionaryBatch);
          if (message === null || message === void 0 ? void 0 : message.isDictionaryBatch()) {
            const header = message.header();
            const buffer = yield this._reader.readMessageBody(message.bodyLength);
            const vector = this._loadDictionaryBatch(header, buffer);
            this.dictionaries.set(header.id, vector);
          }
        }
      });
    }
    _readFooter() {
      return __awaiter(this, void 0, void 0, function* () {
        const { _handle } = this;
        _handle._pending && (yield _handle._pending);
        const offset = _handle.size - magicAndPadding;
        const length = yield _handle.readInt32(offset);
        const buffer = yield _handle.readAt(offset - length, length);
        return Footer_.decode(buffer);
      });
    }
    _readNextMessageAndValidate(type2) {
      return __awaiter(this, void 0, void 0, function* () {
        if (!this._footer) {
          yield this.open();
        }
        if (this._footer && this._recordBatchIndex < this.numRecordBatches) {
          const block = this._footer.getRecordBatch(this._recordBatchIndex);
          if (block && (yield this._handle.seek(block.offset))) {
            return yield this._reader.readMessage(type2);
          }
        }
        return null;
      });
    }
  };
  var RecordBatchJSONReaderImpl = class extends RecordBatchStreamReaderImpl {
    constructor(source, dictionaries) {
      super(source, dictionaries);
    }
    _loadVectors(header, body, types) {
      return new JSONVectorLoader(body, header.nodes, header.buffers, this.dictionaries).visitMany(types);
    }
  };
  function shouldAutoDestroy(self2, options) {
    return options && typeof options["autoDestroy"] === "boolean" ? options["autoDestroy"] : self2["autoDestroy"];
  }
  function* readAllSync(source) {
    const reader = RecordBatchReader.from(source);
    try {
      if (!reader.open({ autoDestroy: false }).closed) {
        do {
          yield reader;
        } while (!reader.reset().open().closed);
      }
    } finally {
      reader.cancel();
    }
  }
  function readAllAsync(source) {
    return __asyncGenerator(this, arguments, function* readAllAsync_1() {
      const reader = yield __await(RecordBatchReader.from(source));
      try {
        if (!(yield __await(reader.open({ autoDestroy: false }))).closed) {
          do {
            yield yield __await(reader);
          } while (!(yield __await(reader.reset().open())).closed);
        }
      } finally {
        yield __await(reader.cancel());
      }
    });
  }
  function fromArrowJSON(source) {
    return new RecordBatchStreamReader(new RecordBatchJSONReaderImpl(source));
  }
  function fromByteStream(source) {
    const bytes = source.peek(magicLength + 7 & ~7);
    return bytes && bytes.byteLength >= 4 ? !checkForMagicArrowString(bytes) ? new RecordBatchStreamReader(new RecordBatchStreamReaderImpl(source)) : new RecordBatchFileReader(new RecordBatchFileReaderImpl(source.read())) : new RecordBatchStreamReader(new RecordBatchStreamReaderImpl(function* () {
    }()));
  }
  function fromAsyncByteStream(source) {
    return __awaiter(this, void 0, void 0, function* () {
      const bytes = yield source.peek(magicLength + 7 & ~7);
      return bytes && bytes.byteLength >= 4 ? !checkForMagicArrowString(bytes) ? new AsyncRecordBatchStreamReader(new AsyncRecordBatchStreamReaderImpl(source)) : new RecordBatchFileReader(new RecordBatchFileReaderImpl(yield source.read())) : new AsyncRecordBatchStreamReader(new AsyncRecordBatchStreamReaderImpl(function() {
        return __asyncGenerator(this, arguments, function* () {
        });
      }()));
    });
  }
  function fromFileHandle(source) {
    return __awaiter(this, void 0, void 0, function* () {
      const { size } = yield source.stat();
      const file = new AsyncRandomAccessFile(source, size);
      if (size >= magicX2AndPadding && checkForMagicArrowString(yield file.readAt(0, magicLength + 7 & ~7))) {
        return new AsyncRecordBatchFileReader(new AsyncRecordBatchFileReaderImpl(file));
      }
      return new AsyncRecordBatchStreamReader(new AsyncRecordBatchStreamReaderImpl(file));
    });
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/visitor/vectorassembler.mjs
  var VectorAssembler = class _VectorAssembler extends Visitor {
    constructor() {
      super();
      this._byteLength = 0;
      this._nodes = [];
      this._buffers = [];
      this._bufferRegions = [];
    }
    /** @nocollapse */
    static assemble(...args) {
      const unwrap = (nodes) => nodes.flatMap((node) => Array.isArray(node) ? unwrap(node) : node instanceof RecordBatch ? node.data.children : node.data);
      const assembler = new _VectorAssembler();
      assembler.visitMany(unwrap(args));
      return assembler;
    }
    visit(data) {
      if (data instanceof Vector) {
        this.visitMany(data.data);
        return this;
      }
      const { type: type2 } = data;
      if (!DataType.isDictionary(type2)) {
        const { length, nullCount } = data;
        if (length > 2147483647) {
          throw new RangeError("Cannot write arrays larger than 2^31 - 1 in length");
        }
        if (!DataType.isNull(type2)) {
          addBuffer.call(this, nullCount <= 0 ? new Uint8Array(0) : truncateBitmap(data.offset, length, data.nullBitmap));
        }
        this.nodes.push(new FieldNode2(length, nullCount));
      }
      return super.visit(data);
    }
    visitNull(_null) {
      return this;
    }
    visitDictionary(data) {
      return this.visit(data.clone(data.type.indices));
    }
    get nodes() {
      return this._nodes;
    }
    get buffers() {
      return this._buffers;
    }
    get byteLength() {
      return this._byteLength;
    }
    get bufferRegions() {
      return this._bufferRegions;
    }
  };
  function addBuffer(values) {
    const byteLength = values.byteLength + 7 & ~7;
    this.buffers.push(values);
    this.bufferRegions.push(new BufferRegion(this._byteLength, byteLength));
    this._byteLength += byteLength;
    return this;
  }
  function assembleUnion(data) {
    const { type: type2, length, typeIds, valueOffsets } = data;
    addBuffer.call(this, typeIds);
    if (type2.mode === UnionMode.Sparse) {
      return assembleNestedVector.call(this, data);
    } else if (type2.mode === UnionMode.Dense) {
      if (data.offset <= 0) {
        addBuffer.call(this, valueOffsets);
        return assembleNestedVector.call(this, data);
      } else {
        const maxChildTypeId = typeIds.reduce((x, y) => Math.max(x, y), typeIds[0]);
        const childLengths = new Int32Array(maxChildTypeId + 1);
        const childOffsets = new Int32Array(maxChildTypeId + 1).fill(-1);
        const shiftedOffsets = new Int32Array(length);
        const unshiftedOffsets = rebaseValueOffsets(-valueOffsets[0], length, valueOffsets);
        for (let typeId, shift, index = -1; ++index < length; ) {
          if ((shift = childOffsets[typeId = typeIds[index]]) === -1) {
            shift = childOffsets[typeId] = unshiftedOffsets[typeId];
          }
          shiftedOffsets[index] = unshiftedOffsets[index] - shift;
          ++childLengths[typeId];
        }
        addBuffer.call(this, shiftedOffsets);
        for (let child, childIndex = -1, numChildren = type2.children.length; ++childIndex < numChildren; ) {
          if (child = data.children[childIndex]) {
            const typeId = type2.typeIds[childIndex];
            const childLength = Math.min(length, childLengths[typeId]);
            this.visit(child.slice(childOffsets[typeId], childLength));
          }
        }
      }
    }
    return this;
  }
  function assembleBoolVector(data) {
    let values;
    if (data.nullCount >= data.length) {
      return addBuffer.call(this, new Uint8Array(0));
    } else if ((values = data.values) instanceof Uint8Array) {
      return addBuffer.call(this, truncateBitmap(data.offset, data.length, values));
    }
    return addBuffer.call(this, packBools(data.values));
  }
  function assembleFlatVector(data) {
    return addBuffer.call(this, data.values.subarray(0, data.length * data.stride));
  }
  function assembleFlatListVector(data) {
    const { length, values, valueOffsets } = data;
    const firstOffset = valueOffsets[0];
    const lastOffset = valueOffsets[length];
    const byteLength = Math.min(lastOffset - firstOffset, values.byteLength - firstOffset);
    addBuffer.call(this, rebaseValueOffsets(-valueOffsets[0], length, valueOffsets));
    addBuffer.call(this, values.subarray(firstOffset, firstOffset + byteLength));
    return this;
  }
  function assembleListVector(data) {
    const { length, valueOffsets } = data;
    if (valueOffsets) {
      addBuffer.call(this, rebaseValueOffsets(valueOffsets[0], length, valueOffsets));
    }
    return this.visit(data.children[0]);
  }
  function assembleNestedVector(data) {
    return this.visitMany(data.type.children.map((_, i) => data.children[i]).filter(Boolean))[0];
  }
  VectorAssembler.prototype.visitBool = assembleBoolVector;
  VectorAssembler.prototype.visitInt = assembleFlatVector;
  VectorAssembler.prototype.visitFloat = assembleFlatVector;
  VectorAssembler.prototype.visitUtf8 = assembleFlatListVector;
  VectorAssembler.prototype.visitBinary = assembleFlatListVector;
  VectorAssembler.prototype.visitFixedSizeBinary = assembleFlatVector;
  VectorAssembler.prototype.visitDate = assembleFlatVector;
  VectorAssembler.prototype.visitTimestamp = assembleFlatVector;
  VectorAssembler.prototype.visitTime = assembleFlatVector;
  VectorAssembler.prototype.visitDecimal = assembleFlatVector;
  VectorAssembler.prototype.visitList = assembleListVector;
  VectorAssembler.prototype.visitStruct = assembleNestedVector;
  VectorAssembler.prototype.visitUnion = assembleUnion;
  VectorAssembler.prototype.visitInterval = assembleFlatVector;
  VectorAssembler.prototype.visitFixedSizeList = assembleListVector;
  VectorAssembler.prototype.visitMap = assembleListVector;

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/writer.mjs
  var RecordBatchWriter = class extends ReadableInterop {
    constructor(options) {
      super();
      this._position = 0;
      this._started = false;
      this._sink = new AsyncByteQueue();
      this._schema = null;
      this._dictionaryBlocks = [];
      this._recordBatchBlocks = [];
      this._dictionaryDeltaOffsets = /* @__PURE__ */ new Map();
      isObject(options) || (options = { autoDestroy: true, writeLegacyIpcFormat: false });
      this._autoDestroy = typeof options.autoDestroy === "boolean" ? options.autoDestroy : true;
      this._writeLegacyIpcFormat = typeof options.writeLegacyIpcFormat === "boolean" ? options.writeLegacyIpcFormat : false;
    }
    /** @nocollapse */
    // @ts-ignore
    static throughNode(options) {
      throw new Error(`"throughNode" not available in this environment`);
    }
    /** @nocollapse */
    static throughDOM(writableStrategy, readableStrategy) {
      throw new Error(`"throughDOM" not available in this environment`);
    }
    toString(sync = false) {
      return this._sink.toString(sync);
    }
    toUint8Array(sync = false) {
      return this._sink.toUint8Array(sync);
    }
    writeAll(input) {
      if (isPromise(input)) {
        return input.then((x) => this.writeAll(x));
      } else if (isAsyncIterable(input)) {
        return writeAllAsync(this, input);
      }
      return writeAll(this, input);
    }
    get closed() {
      return this._sink.closed;
    }
    [Symbol.asyncIterator]() {
      return this._sink[Symbol.asyncIterator]();
    }
    toDOMStream(options) {
      return this._sink.toDOMStream(options);
    }
    toNodeStream(options) {
      return this._sink.toNodeStream(options);
    }
    close() {
      return this.reset()._sink.close();
    }
    abort(reason) {
      return this.reset()._sink.abort(reason);
    }
    finish() {
      this._autoDestroy ? this.close() : this.reset(this._sink, this._schema);
      return this;
    }
    reset(sink = this._sink, schema = null) {
      if (sink === this._sink || sink instanceof AsyncByteQueue) {
        this._sink = sink;
      } else {
        this._sink = new AsyncByteQueue();
        if (sink && isWritableDOMStream(sink)) {
          this.toDOMStream({ type: "bytes" }).pipeTo(sink);
        } else if (sink && isWritableNodeStream(sink)) {
          this.toNodeStream({ objectMode: false }).pipe(sink);
        }
      }
      if (this._started && this._schema) {
        this._writeFooter(this._schema);
      }
      this._started = false;
      this._dictionaryBlocks = [];
      this._recordBatchBlocks = [];
      this._dictionaryDeltaOffsets = /* @__PURE__ */ new Map();
      if (!schema || !compareSchemas(schema, this._schema)) {
        if (schema == null) {
          this._position = 0;
          this._schema = null;
        } else {
          this._started = true;
          this._schema = schema;
          this._writeSchema(schema);
        }
      }
      return this;
    }
    write(payload) {
      let schema = null;
      if (!this._sink) {
        throw new Error(`RecordBatchWriter is closed`);
      } else if (payload == null) {
        return this.finish() && void 0;
      } else if (payload instanceof Table && !(schema = payload.schema)) {
        return this.finish() && void 0;
      } else if (payload instanceof RecordBatch && !(schema = payload.schema)) {
        return this.finish() && void 0;
      }
      if (schema && !compareSchemas(schema, this._schema)) {
        if (this._started && this._autoDestroy) {
          return this.close();
        }
        this.reset(this._sink, schema);
      }
      if (payload instanceof RecordBatch) {
        if (!(payload instanceof _InternalEmptyPlaceholderRecordBatch)) {
          this._writeRecordBatch(payload);
        }
      } else if (payload instanceof Table) {
        this.writeAll(payload.batches);
      } else if (isIterable(payload)) {
        this.writeAll(payload);
      }
    }
    _writeMessage(message, alignment = 8) {
      const a = alignment - 1;
      const buffer = Message2.encode(message);
      const flatbufferSize = buffer.byteLength;
      const prefixSize = !this._writeLegacyIpcFormat ? 8 : 4;
      const alignedSize = flatbufferSize + prefixSize + a & ~a;
      const nPaddingBytes = alignedSize - flatbufferSize - prefixSize;
      if (message.headerType === MessageHeader.RecordBatch) {
        this._recordBatchBlocks.push(new FileBlock(alignedSize, message.bodyLength, this._position));
      } else if (message.headerType === MessageHeader.DictionaryBatch) {
        this._dictionaryBlocks.push(new FileBlock(alignedSize, message.bodyLength, this._position));
      }
      if (!this._writeLegacyIpcFormat) {
        this._write(Int32Array.of(-1));
      }
      this._write(Int32Array.of(alignedSize - prefixSize));
      if (flatbufferSize > 0) {
        this._write(buffer);
      }
      return this._writePadding(nPaddingBytes);
    }
    _write(chunk) {
      if (this._started) {
        const buffer = toUint8Array(chunk);
        if (buffer && buffer.byteLength > 0) {
          this._sink.write(buffer);
          this._position += buffer.byteLength;
        }
      }
      return this;
    }
    _writeSchema(schema) {
      return this._writeMessage(Message2.from(schema));
    }
    // @ts-ignore
    _writeFooter(schema) {
      return this._writeLegacyIpcFormat ? this._write(Int32Array.of(0)) : this._write(Int32Array.of(-1, 0));
    }
    _writeMagic() {
      return this._write(MAGIC);
    }
    _writePadding(nBytes) {
      return nBytes > 0 ? this._write(new Uint8Array(nBytes)) : this;
    }
    _writeRecordBatch(batch) {
      const { byteLength, nodes, bufferRegions, buffers } = VectorAssembler.assemble(batch);
      const recordBatch = new RecordBatch3(batch.numRows, nodes, bufferRegions);
      const message = Message2.from(recordBatch, byteLength);
      return this._writeDictionaries(batch)._writeMessage(message)._writeBodyBuffers(buffers);
    }
    _writeDictionaryBatch(dictionary, id, isDelta = false) {
      this._dictionaryDeltaOffsets.set(id, dictionary.length + (this._dictionaryDeltaOffsets.get(id) || 0));
      const { byteLength, nodes, bufferRegions, buffers } = VectorAssembler.assemble(new Vector([dictionary]));
      const recordBatch = new RecordBatch3(dictionary.length, nodes, bufferRegions);
      const dictionaryBatch = new DictionaryBatch2(recordBatch, id, isDelta);
      const message = Message2.from(dictionaryBatch, byteLength);
      return this._writeMessage(message)._writeBodyBuffers(buffers);
    }
    _writeBodyBuffers(buffers) {
      let buffer;
      let size, padding;
      for (let i = -1, n = buffers.length; ++i < n; ) {
        if ((buffer = buffers[i]) && (size = buffer.byteLength) > 0) {
          this._write(buffer);
          if ((padding = (size + 7 & ~7) - size) > 0) {
            this._writePadding(padding);
          }
        }
      }
      return this;
    }
    _writeDictionaries(batch) {
      for (let [id, dictionary] of batch.dictionaries) {
        let offset = this._dictionaryDeltaOffsets.get(id) || 0;
        if (offset === 0 || (dictionary = dictionary === null || dictionary === void 0 ? void 0 : dictionary.slice(offset)).length > 0) {
          for (const data of dictionary.data) {
            this._writeDictionaryBatch(data, id, offset > 0);
            offset += data.length;
          }
        }
      }
      return this;
    }
  };
  var RecordBatchStreamWriter = class _RecordBatchStreamWriter extends RecordBatchWriter {
    /** @nocollapse */
    static writeAll(input, options) {
      const writer = new _RecordBatchStreamWriter(options);
      if (isPromise(input)) {
        return input.then((x) => writer.writeAll(x));
      } else if (isAsyncIterable(input)) {
        return writeAllAsync(writer, input);
      }
      return writeAll(writer, input);
    }
  };
  var RecordBatchFileWriter = class _RecordBatchFileWriter extends RecordBatchWriter {
    /** @nocollapse */
    static writeAll(input) {
      const writer = new _RecordBatchFileWriter();
      if (isPromise(input)) {
        return input.then((x) => writer.writeAll(x));
      } else if (isAsyncIterable(input)) {
        return writeAllAsync(writer, input);
      }
      return writeAll(writer, input);
    }
    constructor() {
      super();
      this._autoDestroy = true;
    }
    // @ts-ignore
    _writeSchema(schema) {
      return this._writeMagic()._writePadding(2);
    }
    _writeFooter(schema) {
      const buffer = Footer_.encode(new Footer_(schema, MetadataVersion.V4, this._recordBatchBlocks, this._dictionaryBlocks));
      return super._writeFooter(schema)._write(buffer)._write(Int32Array.of(buffer.byteLength))._writeMagic();
    }
  };
  function writeAll(writer, input) {
    let chunks = input;
    if (input instanceof Table) {
      chunks = input.batches;
      writer.reset(void 0, input.schema);
    }
    for (const batch of chunks) {
      writer.write(batch);
    }
    return writer.finish();
  }
  function writeAllAsync(writer, batches) {
    var batches_1, batches_1_1;
    var e_1, _a5;
    return __awaiter(this, void 0, void 0, function* () {
      try {
        for (batches_1 = __asyncValues(batches); batches_1_1 = yield batches_1.next(), !batches_1_1.done; ) {
          const batch = batches_1_1.value;
          writer.write(batch);
        }
      } catch (e_1_1) {
        e_1 = { error: e_1_1 };
      } finally {
        try {
          if (batches_1_1 && !batches_1_1.done && (_a5 = batches_1.return)) yield _a5.call(batches_1);
        } finally {
          if (e_1) throw e_1.error;
        }
      }
      return writer.finish();
    });
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/whatwg/iterable.mjs
  function toDOMStream(source, options) {
    if (isAsyncIterable(source)) {
      return asyncIterableAsReadableDOMStream(source, options);
    }
    if (isIterable(source)) {
      return iterableAsReadableDOMStream(source, options);
    }
    throw new Error(`toDOMStream() must be called with an Iterable or AsyncIterable`);
  }
  function iterableAsReadableDOMStream(source, options) {
    let it = null;
    const bm = (options === null || options === void 0 ? void 0 : options.type) === "bytes" || false;
    const hwm = (options === null || options === void 0 ? void 0 : options.highWaterMark) || Math.pow(2, 24);
    return new ReadableStream(Object.assign(Object.assign({}, options), {
      start(controller) {
        next(controller, it || (it = source[Symbol.iterator]()));
      },
      pull(controller) {
        it ? next(controller, it) : controller.close();
      },
      cancel() {
        ((it === null || it === void 0 ? void 0 : it.return) && it.return() || true) && (it = null);
      }
    }), Object.assign({ highWaterMark: bm ? hwm : void 0 }, options));
    function next(controller, it2) {
      let buf;
      let r = null;
      let size = controller.desiredSize || null;
      while (!(r = it2.next(bm ? size : null)).done) {
        if (ArrayBuffer.isView(r.value) && (buf = toUint8Array(r.value))) {
          size != null && bm && (size = size - buf.byteLength + 1);
          r.value = buf;
        }
        controller.enqueue(r.value);
        if (size != null && --size <= 0) {
          return;
        }
      }
      controller.close();
    }
  }
  function asyncIterableAsReadableDOMStream(source, options) {
    let it = null;
    const bm = (options === null || options === void 0 ? void 0 : options.type) === "bytes" || false;
    const hwm = (options === null || options === void 0 ? void 0 : options.highWaterMark) || Math.pow(2, 24);
    return new ReadableStream(Object.assign(Object.assign({}, options), {
      start(controller) {
        return __awaiter(this, void 0, void 0, function* () {
          yield next(controller, it || (it = source[Symbol.asyncIterator]()));
        });
      },
      pull(controller) {
        return __awaiter(this, void 0, void 0, function* () {
          it ? yield next(controller, it) : controller.close();
        });
      },
      cancel() {
        return __awaiter(this, void 0, void 0, function* () {
          ((it === null || it === void 0 ? void 0 : it.return) && (yield it.return()) || true) && (it = null);
        });
      }
    }), Object.assign({ highWaterMark: bm ? hwm : void 0 }, options));
    function next(controller, it2) {
      return __awaiter(this, void 0, void 0, function* () {
        let buf;
        let r = null;
        let size = controller.desiredSize || null;
        while (!(r = yield it2.next(bm ? size : null)).done) {
          if (ArrayBuffer.isView(r.value) && (buf = toUint8Array(r.value))) {
            size != null && bm && (size = size - buf.byteLength + 1);
            r.value = buf;
          }
          controller.enqueue(r.value);
          if (size != null && --size <= 0) {
            return;
          }
        }
        controller.close();
      });
    }
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/whatwg/builder.mjs
  function builderThroughDOMStream(options) {
    return new BuilderTransform(options);
  }
  var BuilderTransform = class {
    constructor(options) {
      this._numChunks = 0;
      this._finished = false;
      this._bufferedSize = 0;
      const { ["readableStrategy"]: readableStrategy, ["writableStrategy"]: writableStrategy, ["queueingStrategy"]: queueingStrategy = "count" } = options, builderOptions = __rest(options, ["readableStrategy", "writableStrategy", "queueingStrategy"]);
      this._controller = null;
      this._builder = makeBuilder(builderOptions);
      this._getSize = queueingStrategy !== "bytes" ? chunkLength : chunkByteLength;
      const { ["highWaterMark"]: readableHighWaterMark = queueingStrategy === "bytes" ? Math.pow(2, 14) : 1e3 } = Object.assign({}, readableStrategy);
      const { ["highWaterMark"]: writableHighWaterMark = queueingStrategy === "bytes" ? Math.pow(2, 14) : 1e3 } = Object.assign({}, writableStrategy);
      this["readable"] = new ReadableStream({
        ["cancel"]: () => {
          this._builder.clear();
        },
        ["pull"]: (c) => {
          this._maybeFlush(this._builder, this._controller = c);
        },
        ["start"]: (c) => {
          this._maybeFlush(this._builder, this._controller = c);
        }
      }, {
        "highWaterMark": readableHighWaterMark,
        "size": queueingStrategy !== "bytes" ? chunkLength : chunkByteLength
      });
      this["writable"] = new WritableStream({
        ["abort"]: () => {
          this._builder.clear();
        },
        ["write"]: () => {
          this._maybeFlush(this._builder, this._controller);
        },
        ["close"]: () => {
          this._maybeFlush(this._builder.finish(), this._controller);
        }
      }, {
        "highWaterMark": writableHighWaterMark,
        "size": (value) => this._writeValueAndReturnChunkSize(value)
      });
    }
    _writeValueAndReturnChunkSize(value) {
      const bufferedSize = this._bufferedSize;
      this._bufferedSize = this._getSize(this._builder.append(value));
      return this._bufferedSize - bufferedSize;
    }
    _maybeFlush(builder, controller) {
      if (controller == null) {
        return;
      }
      if (this._bufferedSize >= controller.desiredSize) {
        ++this._numChunks && this._enqueue(controller, builder.toVector());
      }
      if (builder.finished) {
        if (builder.length > 0 || this._numChunks === 0) {
          ++this._numChunks && this._enqueue(controller, builder.toVector());
        }
        if (!this._finished && (this._finished = true)) {
          this._enqueue(controller, null);
        }
      }
    }
    _enqueue(controller, chunk) {
      this._bufferedSize = 0;
      this._controller = null;
      chunk == null ? controller.close() : controller.enqueue(chunk);
    }
  };
  var chunkLength = (chunk) => {
    var _a5;
    return (_a5 = chunk === null || chunk === void 0 ? void 0 : chunk.length) !== null && _a5 !== void 0 ? _a5 : 0;
  };
  var chunkByteLength = (chunk) => {
    var _a5;
    return (_a5 = chunk === null || chunk === void 0 ? void 0 : chunk.byteLength) !== null && _a5 !== void 0 ? _a5 : 0;
  };

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/whatwg/reader.mjs
  function recordBatchReaderThroughDOMStream(writableStrategy, readableStrategy) {
    const queue = new AsyncByteQueue();
    let reader = null;
    const readable = new ReadableStream({
      cancel() {
        return __awaiter(this, void 0, void 0, function* () {
          yield queue.close();
        });
      },
      start(controller) {
        return __awaiter(this, void 0, void 0, function* () {
          yield next(controller, reader || (reader = yield open()));
        });
      },
      pull(controller) {
        return __awaiter(this, void 0, void 0, function* () {
          reader ? yield next(controller, reader) : controller.close();
        });
      }
    });
    return { writable: new WritableStream(queue, Object.assign({ "highWaterMark": Math.pow(2, 14) }, writableStrategy)), readable };
    function open() {
      return __awaiter(this, void 0, void 0, function* () {
        return yield (yield RecordBatchReader.from(queue)).open(readableStrategy);
      });
    }
    function next(controller, reader2) {
      return __awaiter(this, void 0, void 0, function* () {
        let size = controller.desiredSize;
        let r = null;
        while (!(r = yield reader2.next()).done) {
          controller.enqueue(r.value);
          if (size != null && --size <= 0) {
            return;
          }
        }
        controller.close();
      });
    }
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/io/whatwg/writer.mjs
  function recordBatchWriterThroughDOMStream(writableStrategy, readableStrategy) {
    const writer = new this(writableStrategy);
    const reader = new AsyncByteStream(writer);
    const readable = new ReadableStream({
      // type: 'bytes',
      cancel() {
        return __awaiter(this, void 0, void 0, function* () {
          yield reader.cancel();
        });
      },
      pull(controller) {
        return __awaiter(this, void 0, void 0, function* () {
          yield next(controller);
        });
      },
      start(controller) {
        return __awaiter(this, void 0, void 0, function* () {
          yield next(controller);
        });
      }
    }, Object.assign({ "highWaterMark": Math.pow(2, 14) }, readableStrategy));
    return { writable: new WritableStream(writer, writableStrategy), readable };
    function next(controller) {
      return __awaiter(this, void 0, void 0, function* () {
        let buf = null;
        let size = controller.desiredSize;
        while (buf = yield reader.read(size || null)) {
          controller.enqueue(buf);
          if (size != null && (size -= buf.byteLength) <= 0) {
            return;
          }
        }
        controller.close();
      });
    }
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/ipc/serialization.mjs
  function tableFromIPC(input) {
    const reader = RecordBatchReader.from(input);
    if (isPromise(reader)) {
      return reader.then((reader2) => tableFromIPC(reader2));
    }
    if (reader.isAsync()) {
      return reader.readAll().then((xs) => new Table(xs));
    }
    return new Table(reader.readAll());
  }
  function tableToIPC(table, type2 = "stream") {
    return (type2 === "stream" ? RecordBatchStreamWriter : RecordBatchFileWriter).writeAll(table).toUint8Array(true);
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/Arrow.mjs
  var util = Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign(Object.assign({}, bn_exports), int_exports), bit_exports), math_exports), buffer_exports), vector_exports), {
    compareSchemas,
    compareFields,
    compareTypes
  });

  // ../../../../../tmp/agrolattice_component_build/node_modules/apache-arrow/Arrow.dom.mjs
  adapters_default.toDOMStream = toDOMStream;
  Builder["throughDOM"] = builderThroughDOMStream;
  RecordBatchReader["throughDOM"] = recordBatchReaderThroughDOMStream;
  RecordBatchFileReader["throughDOM"] = recordBatchReaderThroughDOMStream;
  RecordBatchStreamReader["throughDOM"] = recordBatchReaderThroughDOMStream;
  RecordBatchWriter["throughDOM"] = recordBatchWriterThroughDOMStream;
  RecordBatchFileWriter["throughDOM"] = recordBatchWriterThroughDOMStream;
  RecordBatchStreamWriter["throughDOM"] = recordBatchWriterThroughDOMStream;

  // ../../../../../tmp/agrolattice_component_build/node_modules/streamlit-component-lib/dist/ArrowTable.js
  var ArrowTable = (
    /** @class */
    function() {
      function ArrowTable2(dataBuffer, indexBuffer, columnsBuffer, styler) {
        var _this = this;
        this.getCell = function(rowIndex, columnIndex) {
          var isBlankCell = rowIndex < _this.headerRows && columnIndex < _this.headerColumns;
          var isIndexCell = rowIndex >= _this.headerRows && columnIndex < _this.headerColumns;
          var isColumnsCell = rowIndex < _this.headerRows && columnIndex >= _this.headerColumns;
          if (isBlankCell) {
            var classNames = ["blank"];
            if (columnIndex > 0) {
              classNames.push("level" + rowIndex);
            }
            return {
              type: "blank",
              classNames: classNames.join(" "),
              content: ""
            };
          } else if (isColumnsCell) {
            var dataColumnIndex = columnIndex - _this.headerColumns;
            var classNames = [
              "col_heading",
              "level" + rowIndex,
              "col" + dataColumnIndex
            ];
            return {
              type: "columns",
              classNames: classNames.join(" "),
              content: _this.getContent(_this.columnsTable, dataColumnIndex, rowIndex)
            };
          } else if (isIndexCell) {
            var dataRowIndex = rowIndex - _this.headerRows;
            var classNames = [
              "row_heading",
              "level" + columnIndex,
              "row" + dataRowIndex
            ];
            return {
              type: "index",
              id: "T_".concat(_this.uuid, "level").concat(columnIndex, "_row").concat(dataRowIndex),
              classNames: classNames.join(" "),
              content: _this.getContent(_this.indexTable, dataRowIndex, columnIndex)
            };
          } else {
            var dataRowIndex = rowIndex - _this.headerRows;
            var dataColumnIndex = columnIndex - _this.headerColumns;
            var classNames = [
              "data",
              "row" + dataRowIndex,
              "col" + dataColumnIndex
            ];
            var content = _this.styler ? _this.getContent(_this.styler.displayValuesTable, dataRowIndex, dataColumnIndex) : _this.getContent(_this.dataTable, dataRowIndex, dataColumnIndex);
            return {
              type: "data",
              id: "T_".concat(_this.uuid, "row").concat(dataRowIndex, "_col").concat(dataColumnIndex),
              classNames: classNames.join(" "),
              content
            };
          }
        };
        this.getContent = function(table, rowIndex, columnIndex) {
          var column = table.getChildAt(columnIndex);
          if (column === null) {
            return "";
          }
          var columnTypeId = _this.getColumnTypeId(table, columnIndex);
          switch (columnTypeId) {
            case Type.Timestamp: {
              return _this.nanosToDate(column.get(rowIndex));
            }
            default: {
              return column.get(rowIndex);
            }
          }
        };
        this.dataTable = tableFromIPC(dataBuffer);
        this.indexTable = tableFromIPC(indexBuffer);
        this.columnsTable = tableFromIPC(columnsBuffer);
        this.styler = styler ? {
          caption: styler.caption,
          displayValuesTable: tableFromIPC(styler.displayValues),
          styles: styler.styles,
          uuid: styler.uuid
        } : void 0;
      }
      Object.defineProperty(ArrowTable2.prototype, "rows", {
        get: function() {
          return this.indexTable.numRows + this.columnsTable.numCols;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "columns", {
        get: function() {
          return this.indexTable.numCols + this.columnsTable.numRows;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "headerRows", {
        get: function() {
          return this.rows - this.dataRows;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "headerColumns", {
        get: function() {
          return this.columns - this.dataColumns;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "dataRows", {
        get: function() {
          return this.dataTable.numRows;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "dataColumns", {
        get: function() {
          return this.dataTable.numCols;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "uuid", {
        get: function() {
          return this.styler && this.styler.uuid;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "caption", {
        get: function() {
          return this.styler && this.styler.caption;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "styles", {
        get: function() {
          return this.styler && this.styler.styles;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "table", {
        get: function() {
          return this.dataTable;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "index", {
        get: function() {
          return this.indexTable;
        },
        enumerable: false,
        configurable: true
      });
      Object.defineProperty(ArrowTable2.prototype, "columnTable", {
        get: function() {
          return this.columnsTable;
        },
        enumerable: false,
        configurable: true
      });
      ArrowTable2.prototype.serialize = function() {
        return {
          data: tableToIPC(this.dataTable),
          index: tableToIPC(this.indexTable),
          columns: tableToIPC(this.columnsTable)
        };
      };
      ArrowTable2.prototype.getColumnTypeId = function(table, columnIndex) {
        return table.schema.fields[columnIndex].type.typeId;
      };
      ArrowTable2.prototype.nanosToDate = function(nanos) {
        return new Date(nanos / 1e6);
      };
      return ArrowTable2;
    }()
  );

  // ../../../../../tmp/agrolattice_component_build/node_modules/streamlit-component-lib/dist/streamlit.js
  var __assign = function() {
    __assign = Object.assign || function(t) {
      for (var s, i = 1, n = arguments.length; i < n; i++) {
        s = arguments[i];
        for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
          t[p] = s[p];
      }
      return t;
    };
    return __assign.apply(this, arguments);
  };
  var ComponentMessageType;
  (function(ComponentMessageType2) {
    ComponentMessageType2["COMPONENT_READY"] = "streamlit:componentReady";
    ComponentMessageType2["SET_COMPONENT_VALUE"] = "streamlit:setComponentValue";
    ComponentMessageType2["SET_FRAME_HEIGHT"] = "streamlit:setFrameHeight";
  })(ComponentMessageType || (ComponentMessageType = {}));
  var Streamlit = (
    /** @class */
    function() {
      function Streamlit2() {
      }
      Streamlit2.API_VERSION = 1;
      Streamlit2.RENDER_EVENT = "streamlit:render";
      Streamlit2.events = new EventTarget();
      Streamlit2.registeredMessageListener = false;
      Streamlit2.setComponentReady = function() {
        if (!Streamlit2.registeredMessageListener) {
          window.addEventListener("message", Streamlit2.onMessageEvent);
          Streamlit2.registeredMessageListener = true;
        }
        Streamlit2.sendBackMsg(ComponentMessageType.COMPONENT_READY, {
          apiVersion: Streamlit2.API_VERSION
        });
      };
      Streamlit2.setFrameHeight = function(height) {
        if (height === void 0) {
          height = document.body.scrollHeight;
        }
        if (height === Streamlit2.lastFrameHeight) {
          return;
        }
        Streamlit2.lastFrameHeight = height;
        Streamlit2.sendBackMsg(ComponentMessageType.SET_FRAME_HEIGHT, { height });
      };
      Streamlit2.setComponentValue = function(value) {
        var dataType;
        if (value instanceof ArrowTable) {
          dataType = "dataframe";
          value = value.serialize();
        } else if (isTypedArray(value)) {
          dataType = "bytes";
          value = new Uint8Array(value.buffer);
        } else if (value instanceof ArrayBuffer) {
          dataType = "bytes";
          value = new Uint8Array(value);
        } else {
          dataType = "json";
        }
        Streamlit2.sendBackMsg(ComponentMessageType.SET_COMPONENT_VALUE, {
          value,
          dataType
        });
      };
      Streamlit2.onMessageEvent = function(event) {
        var type2 = event.data["type"];
        switch (type2) {
          case Streamlit2.RENDER_EVENT:
            Streamlit2.onRenderMessage(event.data);
            break;
        }
      };
      Streamlit2.onRenderMessage = function(data) {
        var args = data["args"];
        if (args == null) {
          console.error("Got null args in onRenderMessage. This should never happen");
          args = {};
        }
        var dataframeArgs = data["dfs"] && data["dfs"].length > 0 ? Streamlit2.argsDataframeToObject(data["dfs"]) : {};
        args = __assign(__assign({}, args), dataframeArgs);
        var disabled = Boolean(data["disabled"]);
        var theme = data["theme"];
        if (theme) {
          _injectTheme(theme);
        }
        var eventData = { disabled, args, theme };
        var event = new CustomEvent(Streamlit2.RENDER_EVENT, {
          detail: eventData
        });
        Streamlit2.events.dispatchEvent(event);
      };
      Streamlit2.argsDataframeToObject = function(argsDataframe) {
        var argsDataframeArrow = argsDataframe.map(function(_a5) {
          var key = _a5.key, value = _a5.value;
          return [key, Streamlit2.toArrowTable(value)];
        });
        return Object.fromEntries(argsDataframeArrow);
      };
      Streamlit2.toArrowTable = function(df) {
        var _a5;
        var data = (_a5 = df.data, _a5.data), index = _a5.index, columns = _a5.columns, styler = _a5.styler;
        return new ArrowTable(data, index, columns, styler);
      };
      Streamlit2.sendBackMsg = function(type2, data) {
        window.parent.postMessage(__assign({ isStreamlitMessage: true, type: type2 }, data), "*");
      };
      return Streamlit2;
    }()
  );
  var _injectTheme = function(theme) {
    var style = document.createElement("style");
    document.head.appendChild(style);
    style.innerHTML = "\n    :root {\n      --primary-color: ".concat(theme.primaryColor, ";\n      --background-color: ").concat(theme.backgroundColor, ";\n      --secondary-background-color: ").concat(theme.secondaryBackgroundColor, ";\n      --text-color: ").concat(theme.textColor, ";\n      --font: ").concat(theme.font, ";\n    }\n\n    body {\n      background-color: var(--background-color);\n      color: var(--text-color);\n    }\n  ");
  };
  function isTypedArray(value) {
    var isBigIntArray = false;
    try {
      isBigIntArray = value instanceof BigInt64Array || value instanceof BigUint64Array;
    } catch (e) {
    }
    return value instanceof Int8Array || value instanceof Uint8Array || value instanceof Uint8ClampedArray || value instanceof Int16Array || value instanceof Uint16Array || value instanceof Int32Array || value instanceof Uint32Array || value instanceof Float32Array || value instanceof Float64Array || isBigIntArray;
  }

  // ../../../../../tmp/agrolattice_component_build/node_modules/streamlit-component-lib/dist/StreamlitReact.js
  var __extends = /* @__PURE__ */ function() {
    var extendStatics = function(d, b) {
      extendStatics = Object.setPrototypeOf || { __proto__: [] } instanceof Array && function(d2, b2) {
        d2.__proto__ = b2;
      } || function(d2, b2) {
        for (var p in b2) if (Object.prototype.hasOwnProperty.call(b2, p)) d2[p] = b2[p];
      };
      return extendStatics(d, b);
    };
    return function(d, b) {
      if (typeof b !== "function" && b !== null)
        throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
      extendStatics(d, b);
      function __() {
        this.constructor = d;
      }
      d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
  }();
  var StreamlitComponentBase = (
    /** @class */
    function(_super) {
      __extends(StreamlitComponentBase2, _super);
      function StreamlitComponentBase2() {
        return _super !== null && _super.apply(this, arguments) || this;
      }
      StreamlitComponentBase2.prototype.componentDidMount = function() {
        Streamlit.setFrameHeight();
      };
      StreamlitComponentBase2.prototype.componentDidUpdate = function() {
        Streamlit.setFrameHeight();
      };
      return StreamlitComponentBase2;
    }(import_react.default.PureComponent)
  );

  // components/agrolattice_boundary_editor/src.js
  var import_leaflet = __toESM(require_leaflet_src());

  // ../../../../../tmp/agrolattice_component_build/node_modules/leaflet-draw/dist/leaflet.draw.js
  !function(t, e, i) {
    function o(t2, e2) {
      for (; (t2 = t2.parentElement) && !t2.classList.contains(e2); ) ;
      return t2;
    }
    L.drawVersion = "1.0.4", L.Draw = {}, L.drawLocal = { draw: { toolbar: { actions: { title: "Cancel drawing", text: "Cancel" }, finish: { title: "Finish drawing", text: "Finish" }, undo: { title: "Delete last point drawn", text: "Delete last point" }, buttons: { polyline: "Draw a polyline", polygon: "Draw a polygon", rectangle: "Draw a rectangle", circle: "Draw a circle", marker: "Draw a marker", circlemarker: "Draw a circlemarker" } }, handlers: { circle: { tooltip: { start: "Click and drag to draw circle." }, radius: "Radius" }, circlemarker: { tooltip: { start: "Click map to place circle marker." } }, marker: { tooltip: { start: "Click map to place marker." } }, polygon: { tooltip: { start: "Click to start drawing shape.", cont: "Click to continue drawing shape.", end: "Click first point to close this shape." } }, polyline: { error: "<strong>Error:</strong> shape edges cannot cross!", tooltip: { start: "Click to start drawing line.", cont: "Click to continue drawing line.", end: "Click last point to finish line." } }, rectangle: { tooltip: { start: "Click and drag to draw rectangle." } }, simpleshape: { tooltip: { end: "Release mouse to finish drawing." } } } }, edit: { toolbar: { actions: { save: { title: "Save changes", text: "Save" }, cancel: { title: "Cancel editing, discards all changes", text: "Cancel" }, clearAll: { title: "Clear all layers", text: "Clear All" } }, buttons: { edit: "Edit layers", editDisabled: "No layers to edit", remove: "Delete layers", removeDisabled: "No layers to delete" } }, handlers: { edit: { tooltip: { text: "Drag handles or markers to edit features.", subtext: "Click cancel to undo changes." } }, remove: { tooltip: { text: "Click on a feature to remove." } } } } }, L.Draw.Event = {}, L.Draw.Event.CREATED = "draw:created", L.Draw.Event.EDITED = "draw:edited", L.Draw.Event.DELETED = "draw:deleted", L.Draw.Event.DRAWSTART = "draw:drawstart", L.Draw.Event.DRAWSTOP = "draw:drawstop", L.Draw.Event.DRAWVERTEX = "draw:drawvertex", L.Draw.Event.EDITSTART = "draw:editstart", L.Draw.Event.EDITMOVE = "draw:editmove", L.Draw.Event.EDITRESIZE = "draw:editresize", L.Draw.Event.EDITVERTEX = "draw:editvertex", L.Draw.Event.EDITSTOP = "draw:editstop", L.Draw.Event.DELETESTART = "draw:deletestart", L.Draw.Event.DELETESTOP = "draw:deletestop", L.Draw.Event.TOOLBAROPENED = "draw:toolbaropened", L.Draw.Event.TOOLBARCLOSED = "draw:toolbarclosed", L.Draw.Event.MARKERCONTEXT = "draw:markercontext", L.Draw = L.Draw || {}, L.Draw.Feature = L.Handler.extend({ initialize: function(t2, e2) {
      this._map = t2, this._container = t2._container, this._overlayPane = t2._panes.overlayPane, this._popupPane = t2._panes.popupPane, e2 && e2.shapeOptions && (e2.shapeOptions = L.Util.extend({}, this.options.shapeOptions, e2.shapeOptions)), L.setOptions(this, e2);
      var i2 = L.version.split(".");
      1 === parseInt(i2[0], 10) && parseInt(i2[1], 10) >= 2 ? L.Draw.Feature.include(L.Evented.prototype) : L.Draw.Feature.include(L.Mixin.Events);
    }, enable: function() {
      this._enabled || (L.Handler.prototype.enable.call(this), this.fire("enabled", { handler: this.type }), this._map.fire(L.Draw.Event.DRAWSTART, { layerType: this.type }));
    }, disable: function() {
      this._enabled && (L.Handler.prototype.disable.call(this), this._map.fire(L.Draw.Event.DRAWSTOP, { layerType: this.type }), this.fire("disabled", { handler: this.type }));
    }, addHooks: function() {
      var t2 = this._map;
      t2 && (L.DomUtil.disableTextSelection(), t2.getContainer().focus(), this._tooltip = new L.Draw.Tooltip(this._map), L.DomEvent.on(this._container, "keyup", this._cancelDrawing, this));
    }, removeHooks: function() {
      this._map && (L.DomUtil.enableTextSelection(), this._tooltip.dispose(), this._tooltip = null, L.DomEvent.off(this._container, "keyup", this._cancelDrawing, this));
    }, setOptions: function(t2) {
      L.setOptions(this, t2);
    }, _fireCreatedEvent: function(t2) {
      this._map.fire(L.Draw.Event.CREATED, { layer: t2, layerType: this.type });
    }, _cancelDrawing: function(t2) {
      27 === t2.keyCode && (this._map.fire("draw:canceled", { layerType: this.type }), this.disable());
    } }), L.Draw.Polyline = L.Draw.Feature.extend({ statics: { TYPE: "polyline" }, Poly: L.Polyline, options: { allowIntersection: true, repeatMode: false, drawError: { color: "#b00b00", timeout: 2500 }, icon: new L.DivIcon({ iconSize: new L.Point(8, 8), className: "leaflet-div-icon leaflet-editing-icon" }), touchIcon: new L.DivIcon({ iconSize: new L.Point(20, 20), className: "leaflet-div-icon leaflet-editing-icon leaflet-touch-icon" }), guidelineDistance: 20, maxGuideLineLength: 4e3, shapeOptions: { stroke: true, color: "#3388ff", weight: 4, opacity: 0.5, fill: false, clickable: true }, metric: true, feet: true, nautic: false, showLength: true, zIndexOffset: 2e3, factor: 1, maxPoints: 0 }, initialize: function(t2, e2) {
      L.Browser.touch && (this.options.icon = this.options.touchIcon), this.options.drawError.message = L.drawLocal.draw.handlers.polyline.error, e2 && e2.drawError && (e2.drawError = L.Util.extend({}, this.options.drawError, e2.drawError)), this.type = L.Draw.Polyline.TYPE, L.Draw.Feature.prototype.initialize.call(this, t2, e2);
    }, addHooks: function() {
      L.Draw.Feature.prototype.addHooks.call(this), this._map && (this._markers = [], this._markerGroup = new L.LayerGroup(), this._map.addLayer(this._markerGroup), this._poly = new L.Polyline([], this.options.shapeOptions), this._tooltip.updateContent(this._getTooltipText()), this._mouseMarker || (this._mouseMarker = L.marker(this._map.getCenter(), { icon: L.divIcon({ className: "leaflet-mouse-marker", iconAnchor: [20, 20], iconSize: [40, 40] }), opacity: 0, zIndexOffset: this.options.zIndexOffset })), this._mouseMarker.on("mouseout", this._onMouseOut, this).on("mousemove", this._onMouseMove, this).on("mousedown", this._onMouseDown, this).on("mouseup", this._onMouseUp, this).addTo(this._map), this._map.on("mouseup", this._onMouseUp, this).on("mousemove", this._onMouseMove, this).on("zoomlevelschange", this._onZoomEnd, this).on("touchstart", this._onTouch, this).on("zoomend", this._onZoomEnd, this));
    }, removeHooks: function() {
      L.Draw.Feature.prototype.removeHooks.call(this), this._clearHideErrorTimeout(), this._cleanUpShape(), this._map.removeLayer(this._markerGroup), delete this._markerGroup, delete this._markers, this._map.removeLayer(this._poly), delete this._poly, this._mouseMarker.off("mousedown", this._onMouseDown, this).off("mouseout", this._onMouseOut, this).off("mouseup", this._onMouseUp, this).off("mousemove", this._onMouseMove, this), this._map.removeLayer(this._mouseMarker), delete this._mouseMarker, this._clearGuides(), this._map.off("mouseup", this._onMouseUp, this).off("mousemove", this._onMouseMove, this).off("zoomlevelschange", this._onZoomEnd, this).off("zoomend", this._onZoomEnd, this).off("touchstart", this._onTouch, this).off("click", this._onTouch, this);
    }, deleteLastVertex: function() {
      if (!(this._markers.length <= 1)) {
        var t2 = this._markers.pop(), e2 = this._poly, i2 = e2.getLatLngs(), o2 = i2.splice(-1, 1)[0];
        this._poly.setLatLngs(i2), this._markerGroup.removeLayer(t2), e2.getLatLngs().length < 2 && this._map.removeLayer(e2), this._vertexChanged(o2, false);
      }
    }, addVertex: function(t2) {
      if (this._markers.length >= 2 && !this.options.allowIntersection && this._poly.newLatLngIntersects(t2)) return void this._showErrorTooltip();
      this._errorShown && this._hideErrorTooltip(), this._markers.push(this._createMarker(t2)), this._poly.addLatLng(t2), 2 === this._poly.getLatLngs().length && this._map.addLayer(this._poly), this._vertexChanged(t2, true);
    }, completeShape: function() {
      this._markers.length <= 1 || !this._shapeIsValid() || (this._fireCreatedEvent(), this.disable(), this.options.repeatMode && this.enable());
    }, _finishShape: function() {
      var t2 = this._poly._defaultShape ? this._poly._defaultShape() : this._poly.getLatLngs(), e2 = this._poly.newLatLngIntersects(t2[t2.length - 1]);
      if (!this.options.allowIntersection && e2 || !this._shapeIsValid()) return void this._showErrorTooltip();
      this._fireCreatedEvent(), this.disable(), this.options.repeatMode && this.enable();
    }, _shapeIsValid: function() {
      return true;
    }, _onZoomEnd: function() {
      null !== this._markers && this._updateGuide();
    }, _onMouseMove: function(t2) {
      var e2 = this._map.mouseEventToLayerPoint(t2.originalEvent), i2 = this._map.layerPointToLatLng(e2);
      this._currentLatLng = i2, this._updateTooltip(i2), this._updateGuide(e2), this._mouseMarker.setLatLng(i2), L.DomEvent.preventDefault(t2.originalEvent);
    }, _vertexChanged: function(t2, e2) {
      this._map.fire(L.Draw.Event.DRAWVERTEX, { layers: this._markerGroup }), this._updateFinishHandler(), this._updateRunningMeasure(t2, e2), this._clearGuides(), this._updateTooltip();
    }, _onMouseDown: function(t2) {
      if (!this._clickHandled && !this._touchHandled && !this._disableMarkers) {
        this._onMouseMove(t2), this._clickHandled = true, this._disableNewMarkers();
        var e2 = t2.originalEvent, i2 = e2.clientX, o2 = e2.clientY;
        this._startPoint.call(this, i2, o2);
      }
    }, _startPoint: function(t2, e2) {
      this._mouseDownOrigin = L.point(t2, e2);
    }, _onMouseUp: function(t2) {
      var e2 = t2.originalEvent, i2 = e2.clientX, o2 = e2.clientY;
      this._endPoint.call(this, i2, o2, t2), this._clickHandled = null;
    }, _endPoint: function(e2, i2, o2) {
      if (this._mouseDownOrigin) {
        var a = L.point(e2, i2).distanceTo(this._mouseDownOrigin), n = this._calculateFinishDistance(o2.latlng);
        this.options.maxPoints > 1 && this.options.maxPoints == this._markers.length + 1 ? (this.addVertex(o2.latlng), this._finishShape()) : n < 10 && L.Browser.touch ? this._finishShape() : Math.abs(a) < 9 * (t.devicePixelRatio || 1) && this.addVertex(o2.latlng), this._enableNewMarkers();
      }
      this._mouseDownOrigin = null;
    }, _onTouch: function(t2) {
      var e2, i2, o2 = t2.originalEvent;
      !o2.touches || !o2.touches[0] || this._clickHandled || this._touchHandled || this._disableMarkers || (e2 = o2.touches[0].clientX, i2 = o2.touches[0].clientY, this._disableNewMarkers(), this._touchHandled = true, this._startPoint.call(this, e2, i2), this._endPoint.call(this, e2, i2, t2), this._touchHandled = null), this._clickHandled = null;
    }, _onMouseOut: function() {
      this._tooltip && this._tooltip._onMouseOut.call(this._tooltip);
    }, _calculateFinishDistance: function(t2) {
      var e2;
      if (this._markers.length > 0) {
        var i2;
        if (this.type === L.Draw.Polyline.TYPE) i2 = this._markers[this._markers.length - 1];
        else {
          if (this.type !== L.Draw.Polygon.TYPE) return 1 / 0;
          i2 = this._markers[0];
        }
        var o2 = this._map.latLngToContainerPoint(i2.getLatLng()), a = new L.Marker(t2, { icon: this.options.icon, zIndexOffset: 2 * this.options.zIndexOffset }), n = this._map.latLngToContainerPoint(a.getLatLng());
        e2 = o2.distanceTo(n);
      } else e2 = 1 / 0;
      return e2;
    }, _updateFinishHandler: function() {
      var t2 = this._markers.length;
      t2 > 1 && this._markers[t2 - 1].on("click", this._finishShape, this), t2 > 2 && this._markers[t2 - 2].off("click", this._finishShape, this);
    }, _createMarker: function(t2) {
      var e2 = new L.Marker(t2, { icon: this.options.icon, zIndexOffset: 2 * this.options.zIndexOffset });
      return this._markerGroup.addLayer(e2), e2;
    }, _updateGuide: function(t2) {
      var e2 = this._markers ? this._markers.length : 0;
      e2 > 0 && (t2 = t2 || this._map.latLngToLayerPoint(this._currentLatLng), this._clearGuides(), this._drawGuide(this._map.latLngToLayerPoint(this._markers[e2 - 1].getLatLng()), t2));
    }, _updateTooltip: function(t2) {
      var e2 = this._getTooltipText();
      t2 && this._tooltip.updatePosition(t2), this._errorShown || this._tooltip.updateContent(e2);
    }, _drawGuide: function(t2, e2) {
      var i2, o2, a, n = Math.floor(Math.sqrt(Math.pow(e2.x - t2.x, 2) + Math.pow(e2.y - t2.y, 2))), s = this.options.guidelineDistance, r = this.options.maxGuideLineLength, l = n > r ? n - r : s;
      for (this._guidesContainer || (this._guidesContainer = L.DomUtil.create("div", "leaflet-draw-guides", this._overlayPane)); l < n; l += this.options.guidelineDistance) i2 = l / n, o2 = { x: Math.floor(t2.x * (1 - i2) + i2 * e2.x), y: Math.floor(t2.y * (1 - i2) + i2 * e2.y) }, a = L.DomUtil.create("div", "leaflet-draw-guide-dash", this._guidesContainer), a.style.backgroundColor = this._errorShown ? this.options.drawError.color : this.options.shapeOptions.color, L.DomUtil.setPosition(a, o2);
    }, _updateGuideColor: function(t2) {
      if (this._guidesContainer) for (var e2 = 0, i2 = this._guidesContainer.childNodes.length; e2 < i2; e2++) this._guidesContainer.childNodes[e2].style.backgroundColor = t2;
    }, _clearGuides: function() {
      if (this._guidesContainer) for (; this._guidesContainer.firstChild; ) this._guidesContainer.removeChild(this._guidesContainer.firstChild);
    }, _getTooltipText: function() {
      var t2, e2, i2 = this.options.showLength;
      return 0 === this._markers.length ? t2 = { text: L.drawLocal.draw.handlers.polyline.tooltip.start } : (e2 = i2 ? this._getMeasurementString() : "", t2 = 1 === this._markers.length ? { text: L.drawLocal.draw.handlers.polyline.tooltip.cont, subtext: e2 } : { text: L.drawLocal.draw.handlers.polyline.tooltip.end, subtext: e2 }), t2;
    }, _updateRunningMeasure: function(t2, e2) {
      var i2, o2, a = this._markers.length;
      1 === this._markers.length ? this._measurementRunningTotal = 0 : (i2 = a - (e2 ? 2 : 1), o2 = L.GeometryUtil.isVersion07x() ? t2.distanceTo(this._markers[i2].getLatLng()) * (this.options.factor || 1) : this._map.distance(t2, this._markers[i2].getLatLng()) * (this.options.factor || 1), this._measurementRunningTotal += o2 * (e2 ? 1 : -1));
    }, _getMeasurementString: function() {
      var t2, e2 = this._currentLatLng, i2 = this._markers[this._markers.length - 1].getLatLng();
      return t2 = L.GeometryUtil.isVersion07x() ? i2 && e2 && e2.distanceTo ? this._measurementRunningTotal + e2.distanceTo(i2) * (this.options.factor || 1) : this._measurementRunningTotal || 0 : i2 && e2 ? this._measurementRunningTotal + this._map.distance(e2, i2) * (this.options.factor || 1) : this._measurementRunningTotal || 0, L.GeometryUtil.readableDistance(t2, this.options.metric, this.options.feet, this.options.nautic, this.options.precision);
    }, _showErrorTooltip: function() {
      this._errorShown = true, this._tooltip.showAsError().updateContent({ text: this.options.drawError.message }), this._updateGuideColor(this.options.drawError.color), this._poly.setStyle({ color: this.options.drawError.color }), this._clearHideErrorTimeout(), this._hideErrorTimeout = setTimeout(L.Util.bind(this._hideErrorTooltip, this), this.options.drawError.timeout);
    }, _hideErrorTooltip: function() {
      this._errorShown = false, this._clearHideErrorTimeout(), this._tooltip.removeError().updateContent(this._getTooltipText()), this._updateGuideColor(this.options.shapeOptions.color), this._poly.setStyle({ color: this.options.shapeOptions.color });
    }, _clearHideErrorTimeout: function() {
      this._hideErrorTimeout && (clearTimeout(this._hideErrorTimeout), this._hideErrorTimeout = null);
    }, _disableNewMarkers: function() {
      this._disableMarkers = true;
    }, _enableNewMarkers: function() {
      setTimeout(function() {
        this._disableMarkers = false;
      }.bind(this), 50);
    }, _cleanUpShape: function() {
      this._markers.length > 1 && this._markers[this._markers.length - 1].off("click", this._finishShape, this);
    }, _fireCreatedEvent: function() {
      var t2 = new this.Poly(this._poly.getLatLngs(), this.options.shapeOptions);
      L.Draw.Feature.prototype._fireCreatedEvent.call(this, t2);
    } }), L.Draw.Polygon = L.Draw.Polyline.extend({ statics: { TYPE: "polygon" }, Poly: L.Polygon, options: { showArea: false, showLength: false, shapeOptions: { stroke: true, color: "#3388ff", weight: 4, opacity: 0.5, fill: true, fillColor: null, fillOpacity: 0.2, clickable: true }, metric: true, feet: true, nautic: false, precision: {} }, initialize: function(t2, e2) {
      L.Draw.Polyline.prototype.initialize.call(this, t2, e2), this.type = L.Draw.Polygon.TYPE;
    }, _updateFinishHandler: function() {
      var t2 = this._markers.length;
      1 === t2 && this._markers[0].on("click", this._finishShape, this), t2 > 2 && (this._markers[t2 - 1].on("dblclick", this._finishShape, this), t2 > 3 && this._markers[t2 - 2].off("dblclick", this._finishShape, this));
    }, _getTooltipText: function() {
      var t2, e2;
      return 0 === this._markers.length ? t2 = L.drawLocal.draw.handlers.polygon.tooltip.start : this._markers.length < 3 ? (t2 = L.drawLocal.draw.handlers.polygon.tooltip.cont, e2 = this._getMeasurementString()) : (t2 = L.drawLocal.draw.handlers.polygon.tooltip.end, e2 = this._getMeasurementString()), { text: t2, subtext: e2 };
    }, _getMeasurementString: function() {
      var t2 = this._area, e2 = "";
      return t2 || this.options.showLength ? (this.options.showLength && (e2 = L.Draw.Polyline.prototype._getMeasurementString.call(this)), t2 && (e2 += "<br>" + L.GeometryUtil.readableArea(t2, this.options.metric, this.options.precision)), e2) : null;
    }, _shapeIsValid: function() {
      return this._markers.length >= 3;
    }, _vertexChanged: function(t2, e2) {
      var i2;
      !this.options.allowIntersection && this.options.showArea && (i2 = this._poly.getLatLngs(), this._area = L.GeometryUtil.geodesicArea(i2)), L.Draw.Polyline.prototype._vertexChanged.call(this, t2, e2);
    }, _cleanUpShape: function() {
      var t2 = this._markers.length;
      t2 > 0 && (this._markers[0].off("click", this._finishShape, this), t2 > 2 && this._markers[t2 - 1].off("dblclick", this._finishShape, this));
    } }), L.SimpleShape = {}, L.Draw.SimpleShape = L.Draw.Feature.extend({ options: { repeatMode: false }, initialize: function(t2, e2) {
      this._endLabelText = L.drawLocal.draw.handlers.simpleshape.tooltip.end, L.Draw.Feature.prototype.initialize.call(this, t2, e2);
    }, addHooks: function() {
      L.Draw.Feature.prototype.addHooks.call(this), this._map && (this._mapDraggable = this._map.dragging.enabled(), this._mapDraggable && this._map.dragging.disable(), this._container.style.cursor = "crosshair", this._tooltip.updateContent({ text: this._initialLabelText }), this._map.on("mousedown", this._onMouseDown, this).on("mousemove", this._onMouseMove, this).on("touchstart", this._onMouseDown, this).on("touchmove", this._onMouseMove, this), e.addEventListener("touchstart", L.DomEvent.preventDefault, { passive: false }));
    }, removeHooks: function() {
      L.Draw.Feature.prototype.removeHooks.call(this), this._map && (this._mapDraggable && this._map.dragging.enable(), this._container.style.cursor = "", this._map.off("mousedown", this._onMouseDown, this).off("mousemove", this._onMouseMove, this).off("touchstart", this._onMouseDown, this).off("touchmove", this._onMouseMove, this), L.DomEvent.off(e, "mouseup", this._onMouseUp, this), L.DomEvent.off(e, "touchend", this._onMouseUp, this), e.removeEventListener("touchstart", L.DomEvent.preventDefault), this._shape && (this._map.removeLayer(this._shape), delete this._shape)), this._isDrawing = false;
    }, _getTooltipText: function() {
      return { text: this._endLabelText };
    }, _onMouseDown: function(t2) {
      this._isDrawing = true, this._startLatLng = t2.latlng, L.DomEvent.on(e, "mouseup", this._onMouseUp, this).on(e, "touchend", this._onMouseUp, this).preventDefault(t2.originalEvent);
    }, _onMouseMove: function(t2) {
      var e2 = t2.latlng;
      this._tooltip.updatePosition(e2), this._isDrawing && (this._tooltip.updateContent(this._getTooltipText()), this._drawShape(e2));
    }, _onMouseUp: function() {
      this._shape && this._fireCreatedEvent(), this.disable(), this.options.repeatMode && this.enable();
    } }), L.Draw.Rectangle = L.Draw.SimpleShape.extend({ statics: { TYPE: "rectangle" }, options: { shapeOptions: { stroke: true, color: "#3388ff", weight: 4, opacity: 0.5, fill: true, fillColor: null, fillOpacity: 0.2, clickable: true }, showArea: true, metric: true }, initialize: function(t2, e2) {
      this.type = L.Draw.Rectangle.TYPE, this._initialLabelText = L.drawLocal.draw.handlers.rectangle.tooltip.start, L.Draw.SimpleShape.prototype.initialize.call(this, t2, e2);
    }, disable: function() {
      this._enabled && (this._isCurrentlyTwoClickDrawing = false, L.Draw.SimpleShape.prototype.disable.call(this));
    }, _onMouseUp: function(t2) {
      if (!this._shape && !this._isCurrentlyTwoClickDrawing) return void (this._isCurrentlyTwoClickDrawing = true);
      this._isCurrentlyTwoClickDrawing && !o(t2.target, "leaflet-pane") || L.Draw.SimpleShape.prototype._onMouseUp.call(this);
    }, _drawShape: function(t2) {
      this._shape ? this._shape.setBounds(new L.LatLngBounds(this._startLatLng, t2)) : (this._shape = new L.Rectangle(new L.LatLngBounds(this._startLatLng, t2), this.options.shapeOptions), this._map.addLayer(this._shape));
    }, _fireCreatedEvent: function() {
      var t2 = new L.Rectangle(this._shape.getBounds(), this.options.shapeOptions);
      L.Draw.SimpleShape.prototype._fireCreatedEvent.call(this, t2);
    }, _getTooltipText: function() {
      var t2, e2, i2, o2 = L.Draw.SimpleShape.prototype._getTooltipText.call(this), a = this._shape, n = this.options.showArea;
      return a && (t2 = this._shape._defaultShape ? this._shape._defaultShape() : this._shape.getLatLngs(), e2 = L.GeometryUtil.geodesicArea(t2), i2 = n ? L.GeometryUtil.readableArea(e2, this.options.metric) : ""), { text: o2.text, subtext: i2 };
    } }), L.Draw.Marker = L.Draw.Feature.extend({ statics: { TYPE: "marker" }, options: { icon: new L.Icon.Default(), repeatMode: false, zIndexOffset: 2e3 }, initialize: function(t2, e2) {
      this.type = L.Draw.Marker.TYPE, this._initialLabelText = L.drawLocal.draw.handlers.marker.tooltip.start, L.Draw.Feature.prototype.initialize.call(this, t2, e2);
    }, addHooks: function() {
      L.Draw.Feature.prototype.addHooks.call(this), this._map && (this._tooltip.updateContent({ text: this._initialLabelText }), this._mouseMarker || (this._mouseMarker = L.marker(this._map.getCenter(), { icon: L.divIcon({ className: "leaflet-mouse-marker", iconAnchor: [20, 20], iconSize: [40, 40] }), opacity: 0, zIndexOffset: this.options.zIndexOffset })), this._mouseMarker.on("click", this._onClick, this).addTo(this._map), this._map.on("mousemove", this._onMouseMove, this), this._map.on("click", this._onTouch, this));
    }, removeHooks: function() {
      L.Draw.Feature.prototype.removeHooks.call(this), this._map && (this._map.off("click", this._onClick, this).off("click", this._onTouch, this), this._marker && (this._marker.off("click", this._onClick, this), this._map.removeLayer(this._marker), delete this._marker), this._mouseMarker.off("click", this._onClick, this), this._map.removeLayer(this._mouseMarker), delete this._mouseMarker, this._map.off("mousemove", this._onMouseMove, this));
    }, _onMouseMove: function(t2) {
      var e2 = t2.latlng;
      this._tooltip.updatePosition(e2), this._mouseMarker.setLatLng(e2), this._marker ? (e2 = this._mouseMarker.getLatLng(), this._marker.setLatLng(e2)) : (this._marker = this._createMarker(e2), this._marker.on("click", this._onClick, this), this._map.on("click", this._onClick, this).addLayer(this._marker));
    }, _createMarker: function(t2) {
      return new L.Marker(t2, { icon: this.options.icon, zIndexOffset: this.options.zIndexOffset });
    }, _onClick: function() {
      this._fireCreatedEvent(), this.disable(), this.options.repeatMode && this.enable();
    }, _onTouch: function(t2) {
      this._onMouseMove(t2), this._onClick();
    }, _fireCreatedEvent: function() {
      var t2 = new L.Marker.Touch(this._marker.getLatLng(), { icon: this.options.icon });
      L.Draw.Feature.prototype._fireCreatedEvent.call(this, t2);
    } }), L.Draw.CircleMarker = L.Draw.Marker.extend({ statics: { TYPE: "circlemarker" }, options: { stroke: true, color: "#3388ff", weight: 4, opacity: 0.5, fill: true, fillColor: null, fillOpacity: 0.2, clickable: true, zIndexOffset: 2e3 }, initialize: function(t2, e2) {
      this.type = L.Draw.CircleMarker.TYPE, this._initialLabelText = L.drawLocal.draw.handlers.circlemarker.tooltip.start, L.Draw.Feature.prototype.initialize.call(this, t2, e2);
    }, _fireCreatedEvent: function() {
      var t2 = new L.CircleMarker(this._marker.getLatLng(), this.options);
      L.Draw.Feature.prototype._fireCreatedEvent.call(this, t2);
    }, _createMarker: function(t2) {
      return new L.CircleMarker(t2, this.options);
    } }), L.Draw.Circle = L.Draw.SimpleShape.extend({ statics: { TYPE: "circle" }, options: { shapeOptions: { stroke: true, color: "#3388ff", weight: 4, opacity: 0.5, fill: true, fillColor: null, fillOpacity: 0.2, clickable: true }, showRadius: true, metric: true, feet: true, nautic: false }, initialize: function(t2, e2) {
      this.type = L.Draw.Circle.TYPE, this._initialLabelText = L.drawLocal.draw.handlers.circle.tooltip.start, L.Draw.SimpleShape.prototype.initialize.call(this, t2, e2);
    }, _drawShape: function(t2) {
      if (L.GeometryUtil.isVersion07x()) var e2 = this._startLatLng.distanceTo(t2);
      else var e2 = this._map.distance(this._startLatLng, t2);
      this._shape ? this._shape.setRadius(e2) : (this._shape = new L.Circle(this._startLatLng, e2, this.options.shapeOptions), this._map.addLayer(this._shape));
    }, _fireCreatedEvent: function() {
      var t2 = new L.Circle(this._startLatLng, this._shape.getRadius(), this.options.shapeOptions);
      L.Draw.SimpleShape.prototype._fireCreatedEvent.call(this, t2);
    }, _onMouseMove: function(t2) {
      var e2, i2 = t2.latlng, o2 = this.options.showRadius, a = this.options.metric;
      if (this._tooltip.updatePosition(i2), this._isDrawing) {
        this._drawShape(i2), e2 = this._shape.getRadius().toFixed(1);
        var n = "";
        o2 && (n = L.drawLocal.draw.handlers.circle.radius + ": " + L.GeometryUtil.readableDistance(e2, a, this.options.feet, this.options.nautic)), this._tooltip.updateContent({ text: this._endLabelText, subtext: n });
      }
    } }), L.Edit = L.Edit || {}, L.Edit.Marker = L.Handler.extend({ initialize: function(t2, e2) {
      this._marker = t2, L.setOptions(this, e2);
    }, addHooks: function() {
      var t2 = this._marker;
      t2.dragging.enable(), t2.on("dragend", this._onDragEnd, t2), this._toggleMarkerHighlight();
    }, removeHooks: function() {
      var t2 = this._marker;
      t2.dragging.disable(), t2.off("dragend", this._onDragEnd, t2), this._toggleMarkerHighlight();
    }, _onDragEnd: function(t2) {
      var e2 = t2.target;
      e2.edited = true, this._map.fire(L.Draw.Event.EDITMOVE, { layer: e2 });
    }, _toggleMarkerHighlight: function() {
      var t2 = this._marker._icon;
      t2 && (t2.style.display = "none", L.DomUtil.hasClass(t2, "leaflet-edit-marker-selected") ? (L.DomUtil.removeClass(t2, "leaflet-edit-marker-selected"), this._offsetMarker(t2, -4)) : (L.DomUtil.addClass(t2, "leaflet-edit-marker-selected"), this._offsetMarker(t2, 4)), t2.style.display = "");
    }, _offsetMarker: function(t2, e2) {
      var i2 = parseInt(t2.style.marginTop, 10) - e2, o2 = parseInt(t2.style.marginLeft, 10) - e2;
      t2.style.marginTop = i2 + "px", t2.style.marginLeft = o2 + "px";
    } }), L.Marker.addInitHook(function() {
      L.Edit.Marker && (this.editing = new L.Edit.Marker(this), this.options.editable && this.editing.enable());
    }), L.Edit = L.Edit || {}, L.Edit.Poly = L.Handler.extend({ initialize: function(t2) {
      this.latlngs = [t2._latlngs], t2._holes && (this.latlngs = this.latlngs.concat(t2._holes)), this._poly = t2, this._poly.on("revert-edited", this._updateLatLngs, this);
    }, _defaultShape: function() {
      return L.Polyline._flat ? L.Polyline._flat(this._poly._latlngs) ? this._poly._latlngs : this._poly._latlngs[0] : this._poly._latlngs;
    }, _eachVertexHandler: function(t2) {
      for (var e2 = 0; e2 < this._verticesHandlers.length; e2++) t2(this._verticesHandlers[e2]);
    }, addHooks: function() {
      this._initHandlers(), this._eachVertexHandler(function(t2) {
        t2.addHooks();
      });
    }, removeHooks: function() {
      this._eachVertexHandler(function(t2) {
        t2.removeHooks();
      });
    }, updateMarkers: function() {
      this._eachVertexHandler(function(t2) {
        t2.updateMarkers();
      });
    }, _initHandlers: function() {
      this._verticesHandlers = [];
      for (var t2 = 0; t2 < this.latlngs.length; t2++) this._verticesHandlers.push(new L.Edit.PolyVerticesEdit(this._poly, this.latlngs[t2], this._poly.options.poly));
    }, _updateLatLngs: function(t2) {
      this.latlngs = [t2.layer._latlngs], t2.layer._holes && (this.latlngs = this.latlngs.concat(t2.layer._holes));
    } }), L.Edit.PolyVerticesEdit = L.Handler.extend({ options: { icon: new L.DivIcon({ iconSize: new L.Point(8, 8), className: "leaflet-div-icon leaflet-editing-icon" }), touchIcon: new L.DivIcon({ iconSize: new L.Point(20, 20), className: "leaflet-div-icon leaflet-editing-icon leaflet-touch-icon" }), drawError: { color: "#b00b00", timeout: 1e3 } }, initialize: function(t2, e2, i2) {
      L.Browser.touch && (this.options.icon = this.options.touchIcon), this._poly = t2, i2 && i2.drawError && (i2.drawError = L.Util.extend({}, this.options.drawError, i2.drawError)), this._latlngs = e2, L.setOptions(this, i2);
    }, _defaultShape: function() {
      return L.Polyline._flat ? L.Polyline._flat(this._latlngs) ? this._latlngs : this._latlngs[0] : this._latlngs;
    }, addHooks: function() {
      var t2 = this._poly, e2 = t2._path;
      t2 instanceof L.Polygon || (t2.options.fill = false, t2.options.editing && (t2.options.editing.fill = false)), e2 && t2.options.editing && t2.options.editing.className && (t2.options.original.className && t2.options.original.className.split(" ").forEach(function(t3) {
        L.DomUtil.removeClass(e2, t3);
      }), t2.options.editing.className.split(" ").forEach(function(t3) {
        L.DomUtil.addClass(e2, t3);
      })), t2.setStyle(t2.options.editing), this._poly._map && (this._map = this._poly._map, this._markerGroup || this._initMarkers(), this._poly._map.addLayer(this._markerGroup));
    }, removeHooks: function() {
      var t2 = this._poly, e2 = t2._path;
      e2 && t2.options.editing && t2.options.editing.className && (t2.options.editing.className.split(" ").forEach(function(t3) {
        L.DomUtil.removeClass(e2, t3);
      }), t2.options.original.className && t2.options.original.className.split(" ").forEach(function(t3) {
        L.DomUtil.addClass(e2, t3);
      })), t2.setStyle(t2.options.original), t2._map && (t2._map.removeLayer(this._markerGroup), delete this._markerGroup, delete this._markers);
    }, updateMarkers: function() {
      this._markerGroup.clearLayers(), this._initMarkers();
    }, _initMarkers: function() {
      this._markerGroup || (this._markerGroup = new L.LayerGroup()), this._markers = [];
      var t2, e2, i2, o2, a = this._defaultShape();
      for (t2 = 0, i2 = a.length; t2 < i2; t2++) o2 = this._createMarker(a[t2], t2), o2.on("click", this._onMarkerClick, this), o2.on("contextmenu", this._onContextMenu, this), this._markers.push(o2);
      var n, s;
      for (t2 = 0, e2 = i2 - 1; t2 < i2; e2 = t2++) (0 !== t2 || L.Polygon && this._poly instanceof L.Polygon) && (n = this._markers[e2], s = this._markers[t2], this._createMiddleMarker(n, s), this._updatePrevNext(n, s));
    }, _createMarker: function(t2, e2) {
      var i2 = new L.Marker.Touch(t2, { draggable: true, icon: this.options.icon });
      return i2._origLatLng = t2, i2._index = e2, i2.on("dragstart", this._onMarkerDragStart, this).on("drag", this._onMarkerDrag, this).on("dragend", this._fireEdit, this).on("touchmove", this._onTouchMove, this).on("touchend", this._fireEdit, this).on("MSPointerMove", this._onTouchMove, this).on("MSPointerUp", this._fireEdit, this), this._markerGroup.addLayer(i2), i2;
    }, _onMarkerDragStart: function() {
      this._poly.fire("editstart");
    }, _spliceLatLngs: function() {
      var t2 = this._defaultShape(), e2 = [].splice.apply(t2, arguments);
      return this._poly._convertLatLngs(t2, true), this._poly.redraw(), e2;
    }, _removeMarker: function(t2) {
      var e2 = t2._index;
      this._markerGroup.removeLayer(t2), this._markers.splice(e2, 1), this._spliceLatLngs(e2, 1), this._updateIndexes(e2, -1), t2.off("dragstart", this._onMarkerDragStart, this).off("drag", this._onMarkerDrag, this).off("dragend", this._fireEdit, this).off("touchmove", this._onMarkerDrag, this).off("touchend", this._fireEdit, this).off("click", this._onMarkerClick, this).off("MSPointerMove", this._onTouchMove, this).off("MSPointerUp", this._fireEdit, this);
    }, _fireEdit: function() {
      this._poly.edited = true, this._poly.fire("edit"), this._poly._map.fire(L.Draw.Event.EDITVERTEX, { layers: this._markerGroup, poly: this._poly });
    }, _onMarkerDrag: function(t2) {
      var e2 = t2.target, i2 = this._poly, o2 = L.LatLngUtil.cloneLatLng(e2._origLatLng);
      if (L.extend(e2._origLatLng, e2._latlng), i2.options.poly) {
        var a = i2._map._editTooltip;
        if (!i2.options.poly.allowIntersection && i2.intersects()) {
          L.extend(e2._origLatLng, o2), e2.setLatLng(o2);
          var n = i2.options.color;
          i2.setStyle({ color: this.options.drawError.color }), a && a.updateContent({ text: L.drawLocal.draw.handlers.polyline.error }), setTimeout(function() {
            i2.setStyle({ color: n }), a && a.updateContent({ text: L.drawLocal.edit.handlers.edit.tooltip.text, subtext: L.drawLocal.edit.handlers.edit.tooltip.subtext });
          }, 1e3);
        }
      }
      e2._middleLeft && e2._middleLeft.setLatLng(this._getMiddleLatLng(e2._prev, e2)), e2._middleRight && e2._middleRight.setLatLng(this._getMiddleLatLng(e2, e2._next)), this._poly._bounds._southWest = L.latLng(1 / 0, 1 / 0), this._poly._bounds._northEast = L.latLng(-1 / 0, -1 / 0);
      var s = this._poly.getLatLngs();
      this._poly._convertLatLngs(s, true), this._poly.redraw(), this._poly.fire("editdrag");
    }, _onMarkerClick: function(t2) {
      var e2 = L.Polygon && this._poly instanceof L.Polygon ? 4 : 3, i2 = t2.target;
      this._defaultShape().length < e2 || (this._removeMarker(i2), this._updatePrevNext(i2._prev, i2._next), i2._middleLeft && this._markerGroup.removeLayer(i2._middleLeft), i2._middleRight && this._markerGroup.removeLayer(i2._middleRight), i2._prev && i2._next ? this._createMiddleMarker(i2._prev, i2._next) : i2._prev ? i2._next || (i2._prev._middleRight = null) : i2._next._middleLeft = null, this._fireEdit());
    }, _onContextMenu: function(t2) {
      var e2 = t2.target;
      this._poly;
      this._poly._map.fire(L.Draw.Event.MARKERCONTEXT, { marker: e2, layers: this._markerGroup, poly: this._poly }), L.DomEvent.stopPropagation;
    }, _onTouchMove: function(t2) {
      var e2 = this._map.mouseEventToLayerPoint(t2.originalEvent.touches[0]), i2 = this._map.layerPointToLatLng(e2), o2 = t2.target;
      L.extend(o2._origLatLng, i2), o2._middleLeft && o2._middleLeft.setLatLng(this._getMiddleLatLng(o2._prev, o2)), o2._middleRight && o2._middleRight.setLatLng(this._getMiddleLatLng(o2, o2._next)), this._poly.redraw(), this.updateMarkers();
    }, _updateIndexes: function(t2, e2) {
      this._markerGroup.eachLayer(function(i2) {
        i2._index > t2 && (i2._index += e2);
      });
    }, _createMiddleMarker: function(t2, e2) {
      var i2, o2, a, n = this._getMiddleLatLng(t2, e2), s = this._createMarker(n);
      s.setOpacity(0.6), t2._middleRight = e2._middleLeft = s, o2 = function() {
        s.off("touchmove", o2, this);
        var a2 = e2._index;
        s._index = a2, s.off("click", i2, this).on("click", this._onMarkerClick, this), n.lat = s.getLatLng().lat, n.lng = s.getLatLng().lng, this._spliceLatLngs(a2, 0, n), this._markers.splice(a2, 0, s), s.setOpacity(1), this._updateIndexes(a2, 1), e2._index++, this._updatePrevNext(t2, s), this._updatePrevNext(s, e2), this._poly.fire("editstart");
      }, a = function() {
        s.off("dragstart", o2, this), s.off("dragend", a, this), s.off("touchmove", o2, this), this._createMiddleMarker(t2, s), this._createMiddleMarker(s, e2);
      }, i2 = function() {
        o2.call(this), a.call(this), this._fireEdit();
      }, s.on("click", i2, this).on("dragstart", o2, this).on("dragend", a, this).on("touchmove", o2, this), this._markerGroup.addLayer(s);
    }, _updatePrevNext: function(t2, e2) {
      t2 && (t2._next = e2), e2 && (e2._prev = t2);
    }, _getMiddleLatLng: function(t2, e2) {
      var i2 = this._poly._map, o2 = i2.project(t2.getLatLng()), a = i2.project(e2.getLatLng());
      return i2.unproject(o2._add(a)._divideBy(2));
    } }), L.Polyline.addInitHook(function() {
      this.editing || (L.Edit.Poly && (this.editing = new L.Edit.Poly(this), this.options.editable && this.editing.enable()), this.on("add", function() {
        this.editing && this.editing.enabled() && this.editing.addHooks();
      }), this.on("remove", function() {
        this.editing && this.editing.enabled() && this.editing.removeHooks();
      }));
    }), L.Edit = L.Edit || {}, L.Edit.SimpleShape = L.Handler.extend({ options: { moveIcon: new L.DivIcon({ iconSize: new L.Point(8, 8), className: "leaflet-div-icon leaflet-editing-icon leaflet-edit-move" }), resizeIcon: new L.DivIcon({
      iconSize: new L.Point(8, 8),
      className: "leaflet-div-icon leaflet-editing-icon leaflet-edit-resize"
    }), touchMoveIcon: new L.DivIcon({ iconSize: new L.Point(20, 20), className: "leaflet-div-icon leaflet-editing-icon leaflet-edit-move leaflet-touch-icon" }), touchResizeIcon: new L.DivIcon({ iconSize: new L.Point(20, 20), className: "leaflet-div-icon leaflet-editing-icon leaflet-edit-resize leaflet-touch-icon" }) }, initialize: function(t2, e2) {
      L.Browser.touch && (this.options.moveIcon = this.options.touchMoveIcon, this.options.resizeIcon = this.options.touchResizeIcon), this._shape = t2, L.Util.setOptions(this, e2);
    }, addHooks: function() {
      var t2 = this._shape;
      this._shape._map && (this._map = this._shape._map, t2.setStyle(t2.options.editing), t2._map && (this._map = t2._map, this._markerGroup || this._initMarkers(), this._map.addLayer(this._markerGroup)));
    }, removeHooks: function() {
      var t2 = this._shape;
      if (t2.setStyle(t2.options.original), t2._map) {
        this._unbindMarker(this._moveMarker);
        for (var e2 = 0, i2 = this._resizeMarkers.length; e2 < i2; e2++) this._unbindMarker(this._resizeMarkers[e2]);
        this._resizeMarkers = null, this._map.removeLayer(this._markerGroup), delete this._markerGroup;
      }
      this._map = null;
    }, updateMarkers: function() {
      this._markerGroup.clearLayers(), this._initMarkers();
    }, _initMarkers: function() {
      this._markerGroup || (this._markerGroup = new L.LayerGroup()), this._createMoveMarker(), this._createResizeMarker();
    }, _createMoveMarker: function() {
    }, _createResizeMarker: function() {
    }, _createMarker: function(t2, e2) {
      var i2 = new L.Marker.Touch(t2, { draggable: true, icon: e2, zIndexOffset: 10 });
      return this._bindMarker(i2), this._markerGroup.addLayer(i2), i2;
    }, _bindMarker: function(t2) {
      t2.on("dragstart", this._onMarkerDragStart, this).on("drag", this._onMarkerDrag, this).on("dragend", this._onMarkerDragEnd, this).on("touchstart", this._onTouchStart, this).on("touchmove", this._onTouchMove, this).on("MSPointerMove", this._onTouchMove, this).on("touchend", this._onTouchEnd, this).on("MSPointerUp", this._onTouchEnd, this);
    }, _unbindMarker: function(t2) {
      t2.off("dragstart", this._onMarkerDragStart, this).off("drag", this._onMarkerDrag, this).off("dragend", this._onMarkerDragEnd, this).off("touchstart", this._onTouchStart, this).off("touchmove", this._onTouchMove, this).off("MSPointerMove", this._onTouchMove, this).off("touchend", this._onTouchEnd, this).off("MSPointerUp", this._onTouchEnd, this);
    }, _onMarkerDragStart: function(t2) {
      t2.target.setOpacity(0), this._shape.fire("editstart");
    }, _fireEdit: function() {
      this._shape.edited = true, this._shape.fire("edit");
    }, _onMarkerDrag: function(t2) {
      var e2 = t2.target, i2 = e2.getLatLng();
      e2 === this._moveMarker ? this._move(i2) : this._resize(i2), this._shape.redraw(), this._shape.fire("editdrag");
    }, _onMarkerDragEnd: function(t2) {
      t2.target.setOpacity(1), this._fireEdit();
    }, _onTouchStart: function(t2) {
      if (L.Edit.SimpleShape.prototype._onMarkerDragStart.call(this, t2), "function" == typeof this._getCorners) {
        var e2 = this._getCorners(), i2 = t2.target, o2 = i2._cornerIndex;
        i2.setOpacity(0), this._oppositeCorner = e2[(o2 + 2) % 4], this._toggleCornerMarkers(0, o2);
      }
      this._shape.fire("editstart");
    }, _onTouchMove: function(t2) {
      var e2 = this._map.mouseEventToLayerPoint(t2.originalEvent.touches[0]), i2 = this._map.layerPointToLatLng(e2);
      return t2.target === this._moveMarker ? this._move(i2) : this._resize(i2), this._shape.redraw(), false;
    }, _onTouchEnd: function(t2) {
      t2.target.setOpacity(1), this.updateMarkers(), this._fireEdit();
    }, _move: function() {
    }, _resize: function() {
    } }), L.Edit = L.Edit || {}, L.Edit.Rectangle = L.Edit.SimpleShape.extend({ _createMoveMarker: function() {
      var t2 = this._shape.getBounds(), e2 = t2.getCenter();
      this._moveMarker = this._createMarker(e2, this.options.moveIcon);
    }, _createResizeMarker: function() {
      var t2 = this._getCorners();
      this._resizeMarkers = [];
      for (var e2 = 0, i2 = t2.length; e2 < i2; e2++) this._resizeMarkers.push(this._createMarker(t2[e2], this.options.resizeIcon)), this._resizeMarkers[e2]._cornerIndex = e2;
    }, _onMarkerDragStart: function(t2) {
      L.Edit.SimpleShape.prototype._onMarkerDragStart.call(this, t2);
      var e2 = this._getCorners(), i2 = t2.target, o2 = i2._cornerIndex;
      this._oppositeCorner = e2[(o2 + 2) % 4], this._toggleCornerMarkers(0, o2);
    }, _onMarkerDragEnd: function(t2) {
      var e2, i2, o2 = t2.target;
      o2 === this._moveMarker && (e2 = this._shape.getBounds(), i2 = e2.getCenter(), o2.setLatLng(i2)), this._toggleCornerMarkers(1), this._repositionCornerMarkers(), L.Edit.SimpleShape.prototype._onMarkerDragEnd.call(this, t2);
    }, _move: function(t2) {
      for (var e2, i2 = this._shape._defaultShape ? this._shape._defaultShape() : this._shape.getLatLngs(), o2 = this._shape.getBounds(), a = o2.getCenter(), n = [], s = 0, r = i2.length; s < r; s++) e2 = [i2[s].lat - a.lat, i2[s].lng - a.lng], n.push([t2.lat + e2[0], t2.lng + e2[1]]);
      this._shape.setLatLngs(n), this._repositionCornerMarkers(), this._map.fire(L.Draw.Event.EDITMOVE, { layer: this._shape });
    }, _resize: function(t2) {
      var e2;
      this._shape.setBounds(L.latLngBounds(t2, this._oppositeCorner)), e2 = this._shape.getBounds(), this._moveMarker.setLatLng(e2.getCenter()), this._map.fire(L.Draw.Event.EDITRESIZE, { layer: this._shape });
    }, _getCorners: function() {
      var t2 = this._shape.getBounds();
      return [t2.getNorthWest(), t2.getNorthEast(), t2.getSouthEast(), t2.getSouthWest()];
    }, _toggleCornerMarkers: function(t2) {
      for (var e2 = 0, i2 = this._resizeMarkers.length; e2 < i2; e2++) this._resizeMarkers[e2].setOpacity(t2);
    }, _repositionCornerMarkers: function() {
      for (var t2 = this._getCorners(), e2 = 0, i2 = this._resizeMarkers.length; e2 < i2; e2++) this._resizeMarkers[e2].setLatLng(t2[e2]);
    } }), L.Rectangle.addInitHook(function() {
      L.Edit.Rectangle && (this.editing = new L.Edit.Rectangle(this), this.options.editable && this.editing.enable());
    }), L.Edit = L.Edit || {}, L.Edit.CircleMarker = L.Edit.SimpleShape.extend({ _createMoveMarker: function() {
      var t2 = this._shape.getLatLng();
      this._moveMarker = this._createMarker(t2, this.options.moveIcon);
    }, _createResizeMarker: function() {
      this._resizeMarkers = [];
    }, _move: function(t2) {
      if (this._resizeMarkers.length) {
        var e2 = this._getResizeMarkerPoint(t2);
        this._resizeMarkers[0].setLatLng(e2);
      }
      this._shape.setLatLng(t2), this._map.fire(L.Draw.Event.EDITMOVE, { layer: this._shape });
    } }), L.CircleMarker.addInitHook(function() {
      L.Edit.CircleMarker && (this.editing = new L.Edit.CircleMarker(this), this.options.editable && this.editing.enable()), this.on("add", function() {
        this.editing && this.editing.enabled() && this.editing.addHooks();
      }), this.on("remove", function() {
        this.editing && this.editing.enabled() && this.editing.removeHooks();
      });
    }), L.Edit = L.Edit || {}, L.Edit.Circle = L.Edit.CircleMarker.extend({ _createResizeMarker: function() {
      var t2 = this._shape.getLatLng(), e2 = this._getResizeMarkerPoint(t2);
      this._resizeMarkers = [], this._resizeMarkers.push(this._createMarker(e2, this.options.resizeIcon));
    }, _getResizeMarkerPoint: function(t2) {
      var e2 = this._shape._radius * Math.cos(Math.PI / 4), i2 = this._map.project(t2);
      return this._map.unproject([i2.x + e2, i2.y - e2]);
    }, _resize: function(t2) {
      var e2 = this._moveMarker.getLatLng();
      L.GeometryUtil.isVersion07x() ? radius = e2.distanceTo(t2) : radius = this._map.distance(e2, t2), this._shape.setRadius(radius), this._map.editTooltip && this._map._editTooltip.updateContent({ text: L.drawLocal.edit.handlers.edit.tooltip.subtext + "<br />" + L.drawLocal.edit.handlers.edit.tooltip.text, subtext: L.drawLocal.draw.handlers.circle.radius + ": " + L.GeometryUtil.readableDistance(radius, true, this.options.feet, this.options.nautic) }), this._shape.setRadius(radius), this._map.fire(L.Draw.Event.EDITRESIZE, { layer: this._shape });
    } }), L.Circle.addInitHook(function() {
      L.Edit.Circle && (this.editing = new L.Edit.Circle(this), this.options.editable && this.editing.enable());
    }), L.Map.mergeOptions({ touchExtend: true }), L.Map.TouchExtend = L.Handler.extend({ initialize: function(t2) {
      this._map = t2, this._container = t2._container, this._pane = t2._panes.overlayPane;
    }, addHooks: function() {
      L.DomEvent.on(this._container, "touchstart", this._onTouchStart, this), L.DomEvent.on(this._container, "touchend", this._onTouchEnd, this), L.DomEvent.on(this._container, "touchmove", this._onTouchMove, this), this._detectIE() ? (L.DomEvent.on(this._container, "MSPointerDown", this._onTouchStart, this), L.DomEvent.on(this._container, "MSPointerUp", this._onTouchEnd, this), L.DomEvent.on(this._container, "MSPointerMove", this._onTouchMove, this), L.DomEvent.on(this._container, "MSPointerCancel", this._onTouchCancel, this)) : (L.DomEvent.on(this._container, "touchcancel", this._onTouchCancel, this), L.DomEvent.on(this._container, "touchleave", this._onTouchLeave, this));
    }, removeHooks: function() {
      L.DomEvent.off(this._container, "touchstart", this._onTouchStart, this), L.DomEvent.off(this._container, "touchend", this._onTouchEnd, this), L.DomEvent.off(this._container, "touchmove", this._onTouchMove, this), this._detectIE() ? (L.DomEvent.off(this._container, "MSPointerDown", this._onTouchStart, this), L.DomEvent.off(this._container, "MSPointerUp", this._onTouchEnd, this), L.DomEvent.off(this._container, "MSPointerMove", this._onTouchMove, this), L.DomEvent.off(this._container, "MSPointerCancel", this._onTouchCancel, this)) : (L.DomEvent.off(this._container, "touchcancel", this._onTouchCancel, this), L.DomEvent.off(this._container, "touchleave", this._onTouchLeave, this));
    }, _touchEvent: function(t2, e2) {
      var i2 = {};
      if (void 0 !== t2.touches) {
        if (!t2.touches.length) return;
        i2 = t2.touches[0];
      } else {
        if ("touch" !== t2.pointerType) return;
        if (i2 = t2, !this._filterClick(t2)) return;
      }
      var o2 = this._map.mouseEventToContainerPoint(i2), a = this._map.mouseEventToLayerPoint(i2), n = this._map.layerPointToLatLng(a);
      this._map.fire(e2, { latlng: n, layerPoint: a, containerPoint: o2, pageX: i2.pageX, pageY: i2.pageY, originalEvent: t2 });
    }, _filterClick: function(t2) {
      var e2 = t2.timeStamp || t2.originalEvent.timeStamp, i2 = L.DomEvent._lastClick && e2 - L.DomEvent._lastClick;
      return i2 && i2 > 100 && i2 < 500 || t2.target._simulatedClick && !t2._simulated ? (L.DomEvent.stop(t2), false) : (L.DomEvent._lastClick = e2, true);
    }, _onTouchStart: function(t2) {
      if (this._map._loaded) {
        this._touchEvent(t2, "touchstart");
      }
    }, _onTouchEnd: function(t2) {
      if (this._map._loaded) {
        this._touchEvent(t2, "touchend");
      }
    }, _onTouchCancel: function(t2) {
      if (this._map._loaded) {
        var e2 = "touchcancel";
        this._detectIE() && (e2 = "pointercancel"), this._touchEvent(t2, e2);
      }
    }, _onTouchLeave: function(t2) {
      if (this._map._loaded) {
        this._touchEvent(t2, "touchleave");
      }
    }, _onTouchMove: function(t2) {
      if (this._map._loaded) {
        this._touchEvent(t2, "touchmove");
      }
    }, _detectIE: function() {
      var e2 = t.navigator.userAgent, i2 = e2.indexOf("MSIE ");
      if (i2 > 0) return parseInt(e2.substring(i2 + 5, e2.indexOf(".", i2)), 10);
      if (e2.indexOf("Trident/") > 0) {
        var o2 = e2.indexOf("rv:");
        return parseInt(e2.substring(o2 + 3, e2.indexOf(".", o2)), 10);
      }
      var a = e2.indexOf("Edge/");
      return a > 0 && parseInt(e2.substring(a + 5, e2.indexOf(".", a)), 10);
    } }), L.Map.addInitHook("addHandler", "touchExtend", L.Map.TouchExtend), L.Marker.Touch = L.Marker.extend({ _initInteraction: function() {
      return this.addInteractiveTarget ? L.Marker.prototype._initInteraction.apply(this) : this._initInteractionLegacy();
    }, _initInteractionLegacy: function() {
      if (this.options.clickable) {
        var t2 = this._icon, e2 = ["dblclick", "mousedown", "mouseover", "mouseout", "contextmenu", "touchstart", "touchend", "touchmove"];
        this._detectIE ? e2.concat(["MSPointerDown", "MSPointerUp", "MSPointerMove", "MSPointerCancel"]) : e2.concat(["touchcancel"]), L.DomUtil.addClass(t2, "leaflet-clickable"), L.DomEvent.on(t2, "click", this._onMouseClick, this), L.DomEvent.on(t2, "keypress", this._onKeyPress, this);
        for (var i2 = 0; i2 < e2.length; i2++) L.DomEvent.on(t2, e2[i2], this._fireMouseEvent, this);
        L.Handler.MarkerDrag && (this.dragging = new L.Handler.MarkerDrag(this), this.options.draggable && this.dragging.enable());
      }
    }, _detectIE: function() {
      var e2 = t.navigator.userAgent, i2 = e2.indexOf("MSIE ");
      if (i2 > 0) return parseInt(e2.substring(i2 + 5, e2.indexOf(".", i2)), 10);
      if (e2.indexOf("Trident/") > 0) {
        var o2 = e2.indexOf("rv:");
        return parseInt(e2.substring(o2 + 3, e2.indexOf(".", o2)), 10);
      }
      var a = e2.indexOf("Edge/");
      return a > 0 && parseInt(e2.substring(a + 5, e2.indexOf(".", a)), 10);
    } }), L.LatLngUtil = { cloneLatLngs: function(t2) {
      for (var e2 = [], i2 = 0, o2 = t2.length; i2 < o2; i2++) Array.isArray(t2[i2]) ? e2.push(L.LatLngUtil.cloneLatLngs(t2[i2])) : e2.push(this.cloneLatLng(t2[i2]));
      return e2;
    }, cloneLatLng: function(t2) {
      return L.latLng(t2.lat, t2.lng);
    } }, function() {
      var t2 = { km: 2, ha: 2, m: 0, mi: 2, ac: 2, yd: 0, ft: 0, nm: 2 };
      L.GeometryUtil = L.extend(L.GeometryUtil || {}, { geodesicArea: function(t3) {
        var e2, i2, o2 = t3.length, a = 0, n = Math.PI / 180;
        if (o2 > 2) {
          for (var s = 0; s < o2; s++) e2 = t3[s], i2 = t3[(s + 1) % o2], a += (i2.lng - e2.lng) * n * (2 + Math.sin(e2.lat * n) + Math.sin(i2.lat * n));
          a = 6378137 * a * 6378137 / 2;
        }
        return Math.abs(a);
      }, formattedNumber: function(t3, e2) {
        var i2 = parseFloat(t3).toFixed(e2), o2 = L.drawLocal.format && L.drawLocal.format.numeric, a = o2 && o2.delimiters, n = a && a.thousands, s = a && a.decimal;
        if (n || s) {
          var r = i2.split(".");
          i2 = n ? r[0].replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1" + n) : r[0], s = s || ".", r.length > 1 && (i2 = i2 + s + r[1]);
        }
        return i2;
      }, readableArea: function(e2, i2, o2) {
        var a, n, o2 = L.Util.extend({}, t2, o2);
        return i2 ? (n = ["ha", "m"], type = typeof i2, "string" === type ? n = [i2] : "boolean" !== type && (n = i2), a = e2 >= 1e6 && -1 !== n.indexOf("km") ? L.GeometryUtil.formattedNumber(1e-6 * e2, o2.km) + " km\xB2" : e2 >= 1e4 && -1 !== n.indexOf("ha") ? L.GeometryUtil.formattedNumber(1e-4 * e2, o2.ha) + " ha" : L.GeometryUtil.formattedNumber(e2, o2.m) + " m\xB2") : (e2 /= 0.836127, a = e2 >= 3097600 ? L.GeometryUtil.formattedNumber(e2 / 3097600, o2.mi) + " mi\xB2" : e2 >= 4840 ? L.GeometryUtil.formattedNumber(e2 / 4840, o2.ac) + " acres" : L.GeometryUtil.formattedNumber(e2, o2.yd) + " yd\xB2"), a;
      }, readableDistance: function(e2, i2, o2, a, n) {
        var s, n = L.Util.extend({}, t2, n);
        switch (i2 ? "string" == typeof i2 ? i2 : "metric" : o2 ? "feet" : a ? "nauticalMile" : "yards") {
          case "metric":
            s = e2 > 1e3 ? L.GeometryUtil.formattedNumber(e2 / 1e3, n.km) + " km" : L.GeometryUtil.formattedNumber(e2, n.m) + " m";
            break;
          case "feet":
            e2 *= 3.28083, s = L.GeometryUtil.formattedNumber(e2, n.ft) + " ft";
            break;
          case "nauticalMile":
            e2 *= 0.53996, s = L.GeometryUtil.formattedNumber(e2 / 1e3, n.nm) + " nm";
            break;
          case "yards":
          default:
            e2 *= 1.09361, s = e2 > 1760 ? L.GeometryUtil.formattedNumber(e2 / 1760, n.mi) + " miles" : L.GeometryUtil.formattedNumber(e2, n.yd) + " yd";
        }
        return s;
      }, isVersion07x: function() {
        var t3 = L.version.split(".");
        return 0 === parseInt(t3[0], 10) && 7 === parseInt(t3[1], 10);
      } });
    }(), L.Util.extend(L.LineUtil, { segmentsIntersect: function(t2, e2, i2, o2) {
      return this._checkCounterclockwise(t2, i2, o2) !== this._checkCounterclockwise(e2, i2, o2) && this._checkCounterclockwise(t2, e2, i2) !== this._checkCounterclockwise(t2, e2, o2);
    }, _checkCounterclockwise: function(t2, e2, i2) {
      return (i2.y - t2.y) * (e2.x - t2.x) > (e2.y - t2.y) * (i2.x - t2.x);
    } }), L.Polyline.include({ intersects: function() {
      var t2, e2, i2, o2 = this._getProjectedPoints(), a = o2 ? o2.length : 0;
      if (this._tooFewPointsForIntersection()) return false;
      for (t2 = a - 1; t2 >= 3; t2--) if (e2 = o2[t2 - 1], i2 = o2[t2], this._lineSegmentsIntersectsRange(e2, i2, t2 - 2)) return true;
      return false;
    }, newLatLngIntersects: function(t2, e2) {
      return !!this._map && this.newPointIntersects(this._map.latLngToLayerPoint(t2), e2);
    }, newPointIntersects: function(t2, e2) {
      var i2 = this._getProjectedPoints(), o2 = i2 ? i2.length : 0, a = i2 ? i2[o2 - 1] : null, n = o2 - 2;
      return !this._tooFewPointsForIntersection(1) && this._lineSegmentsIntersectsRange(a, t2, n, e2 ? 1 : 0);
    }, _tooFewPointsForIntersection: function(t2) {
      var e2 = this._getProjectedPoints(), i2 = e2 ? e2.length : 0;
      return i2 += t2 || 0, !e2 || i2 <= 3;
    }, _lineSegmentsIntersectsRange: function(t2, e2, i2, o2) {
      var a, n, s = this._getProjectedPoints();
      o2 = o2 || 0;
      for (var r = i2; r > o2; r--) if (a = s[r - 1], n = s[r], L.LineUtil.segmentsIntersect(t2, e2, a, n)) return true;
      return false;
    }, _getProjectedPoints: function() {
      if (!this._defaultShape) return this._originalPoints;
      for (var t2 = [], e2 = this._defaultShape(), i2 = 0; i2 < e2.length; i2++) t2.push(this._map.latLngToLayerPoint(e2[i2]));
      return t2;
    } }), L.Polygon.include({ intersects: function() {
      var t2, e2, i2, o2, a = this._getProjectedPoints();
      return !this._tooFewPointsForIntersection() && (!!L.Polyline.prototype.intersects.call(this) || (t2 = a.length, e2 = a[0], i2 = a[t2 - 1], o2 = t2 - 2, this._lineSegmentsIntersectsRange(i2, e2, o2, 1)));
    } }), L.Control.Draw = L.Control.extend({ options: { position: "topleft", draw: {}, edit: false }, initialize: function(t2) {
      if (L.version < "0.7") throw new Error("Leaflet.draw 0.2.3+ requires Leaflet 0.7.0+. Download latest from https://github.com/Leaflet/Leaflet/");
      L.Control.prototype.initialize.call(this, t2);
      var e2;
      this._toolbars = {}, L.DrawToolbar && this.options.draw && (e2 = new L.DrawToolbar(this.options.draw), this._toolbars[L.DrawToolbar.TYPE] = e2, this._toolbars[L.DrawToolbar.TYPE].on("enable", this._toolbarEnabled, this)), L.EditToolbar && this.options.edit && (e2 = new L.EditToolbar(this.options.edit), this._toolbars[L.EditToolbar.TYPE] = e2, this._toolbars[L.EditToolbar.TYPE].on("enable", this._toolbarEnabled, this)), L.toolbar = this;
    }, onAdd: function(t2) {
      var e2, i2 = L.DomUtil.create("div", "leaflet-draw"), o2 = false;
      for (var a in this._toolbars) this._toolbars.hasOwnProperty(a) && (e2 = this._toolbars[a].addToolbar(t2)) && (o2 || (L.DomUtil.hasClass(e2, "leaflet-draw-toolbar-top") || L.DomUtil.addClass(e2.childNodes[0], "leaflet-draw-toolbar-top"), o2 = true), i2.appendChild(e2));
      return i2;
    }, onRemove: function() {
      for (var t2 in this._toolbars) this._toolbars.hasOwnProperty(t2) && this._toolbars[t2].removeToolbar();
    }, setDrawingOptions: function(t2) {
      for (var e2 in this._toolbars) this._toolbars[e2] instanceof L.DrawToolbar && this._toolbars[e2].setOptions(t2);
    }, _toolbarEnabled: function(t2) {
      var e2 = t2.target;
      for (var i2 in this._toolbars) this._toolbars[i2] !== e2 && this._toolbars[i2].disable();
    } }), L.Map.mergeOptions({ drawControlTooltips: true, drawControl: false }), L.Map.addInitHook(function() {
      this.options.drawControl && (this.drawControl = new L.Control.Draw(), this.addControl(this.drawControl));
    }), L.Toolbar = L.Class.extend({ initialize: function(t2) {
      L.setOptions(this, t2), this._modes = {}, this._actionButtons = [], this._activeMode = null;
      var e2 = L.version.split(".");
      1 === parseInt(e2[0], 10) && parseInt(e2[1], 10) >= 2 ? L.Toolbar.include(L.Evented.prototype) : L.Toolbar.include(L.Mixin.Events);
    }, enabled: function() {
      return null !== this._activeMode;
    }, disable: function() {
      this.enabled() && this._activeMode.handler.disable();
    }, addToolbar: function(t2) {
      var e2, i2 = L.DomUtil.create("div", "leaflet-draw-section"), o2 = 0, a = this._toolbarClass || "", n = this.getModeHandlers(t2);
      for (this._toolbarContainer = L.DomUtil.create("div", "leaflet-draw-toolbar leaflet-bar"), this._map = t2, e2 = 0; e2 < n.length; e2++) n[e2].enabled && this._initModeHandler(n[e2].handler, this._toolbarContainer, o2++, a, n[e2].title);
      if (o2) return this._lastButtonIndex = --o2, this._actionsContainer = L.DomUtil.create("ul", "leaflet-draw-actions"), i2.appendChild(this._toolbarContainer), i2.appendChild(this._actionsContainer), i2;
    }, removeToolbar: function() {
      for (var t2 in this._modes) this._modes.hasOwnProperty(t2) && (this._disposeButton(this._modes[t2].button, this._modes[t2].handler.enable, this._modes[t2].handler), this._modes[t2].handler.disable(), this._modes[t2].handler.off("enabled", this._handlerActivated, this).off("disabled", this._handlerDeactivated, this));
      this._modes = {};
      for (var e2 = 0, i2 = this._actionButtons.length; e2 < i2; e2++) this._disposeButton(this._actionButtons[e2].button, this._actionButtons[e2].callback, this);
      this._actionButtons = [], this._actionsContainer = null;
    }, _initModeHandler: function(t2, e2, i2, o2, a) {
      var n = t2.type;
      this._modes[n] = {}, this._modes[n].handler = t2, this._modes[n].button = this._createButton({ type: n, title: a, className: o2 + "-" + n, container: e2, callback: this._modes[n].handler.enable, context: this._modes[n].handler }), this._modes[n].buttonIndex = i2, this._modes[n].handler.on("enabled", this._handlerActivated, this).on("disabled", this._handlerDeactivated, this);
    }, _detectIOS: function() {
      return /iPad|iPhone|iPod/.test(navigator.userAgent) && !t.MSStream;
    }, _createButton: function(t2) {
      var e2 = L.DomUtil.create("a", t2.className || "", t2.container), i2 = L.DomUtil.create("span", "sr-only", t2.container);
      e2.href = "#", e2.appendChild(i2), t2.title && (e2.title = t2.title, i2.innerHTML = t2.title), t2.text && (e2.innerHTML = t2.text, i2.innerHTML = t2.text);
      var o2 = this._detectIOS() ? "touchstart" : "click";
      return L.DomEvent.on(e2, "click", L.DomEvent.stopPropagation).on(e2, "mousedown", L.DomEvent.stopPropagation).on(e2, "dblclick", L.DomEvent.stopPropagation).on(e2, "touchstart", L.DomEvent.stopPropagation).on(e2, "click", L.DomEvent.preventDefault).on(e2, o2, t2.callback, t2.context), e2;
    }, _disposeButton: function(t2, e2) {
      var i2 = this._detectIOS() ? "touchstart" : "click";
      L.DomEvent.off(t2, "click", L.DomEvent.stopPropagation).off(t2, "mousedown", L.DomEvent.stopPropagation).off(t2, "dblclick", L.DomEvent.stopPropagation).off(t2, "touchstart", L.DomEvent.stopPropagation).off(t2, "click", L.DomEvent.preventDefault).off(t2, i2, e2);
    }, _handlerActivated: function(t2) {
      this.disable(), this._activeMode = this._modes[t2.handler], L.DomUtil.addClass(this._activeMode.button, "leaflet-draw-toolbar-button-enabled"), this._showActionsToolbar(), this.fire("enable");
    }, _handlerDeactivated: function() {
      this._hideActionsToolbar(), L.DomUtil.removeClass(this._activeMode.button, "leaflet-draw-toolbar-button-enabled"), this._activeMode = null, this.fire("disable");
    }, _createActions: function(t2) {
      var e2, i2, o2, a, n = this._actionsContainer, s = this.getActions(t2), r = s.length;
      for (i2 = 0, o2 = this._actionButtons.length; i2 < o2; i2++) this._disposeButton(this._actionButtons[i2].button, this._actionButtons[i2].callback);
      for (this._actionButtons = []; n.firstChild; ) n.removeChild(n.firstChild);
      for (var l = 0; l < r; l++) "enabled" in s[l] && !s[l].enabled || (e2 = L.DomUtil.create("li", "", n), a = this._createButton({ title: s[l].title, text: s[l].text, container: e2, callback: s[l].callback, context: s[l].context }), this._actionButtons.push({ button: a, callback: s[l].callback }));
    }, _showActionsToolbar: function() {
      var t2 = this._activeMode.buttonIndex, e2 = this._lastButtonIndex, i2 = this._activeMode.button.offsetTop - 1;
      this._createActions(this._activeMode.handler), this._actionsContainer.style.top = i2 + "px", 0 === t2 && (L.DomUtil.addClass(this._toolbarContainer, "leaflet-draw-toolbar-notop"), L.DomUtil.addClass(this._actionsContainer, "leaflet-draw-actions-top")), t2 === e2 && (L.DomUtil.addClass(this._toolbarContainer, "leaflet-draw-toolbar-nobottom"), L.DomUtil.addClass(this._actionsContainer, "leaflet-draw-actions-bottom")), this._actionsContainer.style.display = "block", this._map.fire(L.Draw.Event.TOOLBAROPENED);
    }, _hideActionsToolbar: function() {
      this._actionsContainer.style.display = "none", L.DomUtil.removeClass(this._toolbarContainer, "leaflet-draw-toolbar-notop"), L.DomUtil.removeClass(this._toolbarContainer, "leaflet-draw-toolbar-nobottom"), L.DomUtil.removeClass(this._actionsContainer, "leaflet-draw-actions-top"), L.DomUtil.removeClass(this._actionsContainer, "leaflet-draw-actions-bottom"), this._map.fire(L.Draw.Event.TOOLBARCLOSED);
    } }), L.Draw = L.Draw || {}, L.Draw.Tooltip = L.Class.extend({ initialize: function(t2) {
      this._map = t2, this._popupPane = t2._panes.popupPane, this._visible = false, this._container = t2.options.drawControlTooltips ? L.DomUtil.create("div", "leaflet-draw-tooltip", this._popupPane) : null, this._singleLineLabel = false, this._map.on("mouseout", this._onMouseOut, this);
    }, dispose: function() {
      this._map.off("mouseout", this._onMouseOut, this), this._container && (this._popupPane.removeChild(this._container), this._container = null);
    }, updateContent: function(t2) {
      return this._container ? (t2.subtext = t2.subtext || "", 0 !== t2.subtext.length || this._singleLineLabel ? t2.subtext.length > 0 && this._singleLineLabel && (L.DomUtil.removeClass(this._container, "leaflet-draw-tooltip-single"), this._singleLineLabel = false) : (L.DomUtil.addClass(this._container, "leaflet-draw-tooltip-single"), this._singleLineLabel = true), this._container.innerHTML = (t2.subtext.length > 0 ? '<span class="leaflet-draw-tooltip-subtext">' + t2.subtext + "</span><br />" : "") + "<span>" + t2.text + "</span>", t2.text || t2.subtext ? (this._visible = true, this._container.style.visibility = "inherit") : (this._visible = false, this._container.style.visibility = "hidden"), this) : this;
    }, updatePosition: function(t2) {
      var e2 = this._map.latLngToLayerPoint(t2), i2 = this._container;
      return this._container && (this._visible && (i2.style.visibility = "inherit"), L.DomUtil.setPosition(i2, e2)), this;
    }, showAsError: function() {
      return this._container && L.DomUtil.addClass(this._container, "leaflet-error-draw-tooltip"), this;
    }, removeError: function() {
      return this._container && L.DomUtil.removeClass(this._container, "leaflet-error-draw-tooltip"), this;
    }, _onMouseOut: function() {
      this._container && (this._container.style.visibility = "hidden");
    } }), L.DrawToolbar = L.Toolbar.extend({ statics: { TYPE: "draw" }, options: { polyline: {}, polygon: {}, rectangle: {}, circle: {}, marker: {}, circlemarker: {} }, initialize: function(t2) {
      for (var e2 in this.options) this.options.hasOwnProperty(e2) && t2[e2] && (t2[e2] = L.extend({}, this.options[e2], t2[e2]));
      this._toolbarClass = "leaflet-draw-draw", L.Toolbar.prototype.initialize.call(this, t2);
    }, getModeHandlers: function(t2) {
      return [{ enabled: this.options.polyline, handler: new L.Draw.Polyline(t2, this.options.polyline), title: L.drawLocal.draw.toolbar.buttons.polyline }, { enabled: this.options.polygon, handler: new L.Draw.Polygon(t2, this.options.polygon), title: L.drawLocal.draw.toolbar.buttons.polygon }, { enabled: this.options.rectangle, handler: new L.Draw.Rectangle(t2, this.options.rectangle), title: L.drawLocal.draw.toolbar.buttons.rectangle }, { enabled: this.options.circle, handler: new L.Draw.Circle(t2, this.options.circle), title: L.drawLocal.draw.toolbar.buttons.circle }, { enabled: this.options.marker, handler: new L.Draw.Marker(t2, this.options.marker), title: L.drawLocal.draw.toolbar.buttons.marker }, { enabled: this.options.circlemarker, handler: new L.Draw.CircleMarker(t2, this.options.circlemarker), title: L.drawLocal.draw.toolbar.buttons.circlemarker }];
    }, getActions: function(t2) {
      return [{ enabled: t2.completeShape, title: L.drawLocal.draw.toolbar.finish.title, text: L.drawLocal.draw.toolbar.finish.text, callback: t2.completeShape, context: t2 }, { enabled: t2.deleteLastVertex, title: L.drawLocal.draw.toolbar.undo.title, text: L.drawLocal.draw.toolbar.undo.text, callback: t2.deleteLastVertex, context: t2 }, { title: L.drawLocal.draw.toolbar.actions.title, text: L.drawLocal.draw.toolbar.actions.text, callback: this.disable, context: this }];
    }, setOptions: function(t2) {
      L.setOptions(this, t2);
      for (var e2 in this._modes) this._modes.hasOwnProperty(e2) && t2.hasOwnProperty(e2) && this._modes[e2].handler.setOptions(t2[e2]);
    } }), L.EditToolbar = L.Toolbar.extend({ statics: { TYPE: "edit" }, options: { edit: { selectedPathOptions: { dashArray: "10, 10", fill: true, fillColor: "#fe57a1", fillOpacity: 0.1, maintainColor: false } }, remove: {}, poly: null, featureGroup: null }, initialize: function(t2) {
      t2.edit && (void 0 === t2.edit.selectedPathOptions && (t2.edit.selectedPathOptions = this.options.edit.selectedPathOptions), t2.edit.selectedPathOptions = L.extend({}, this.options.edit.selectedPathOptions, t2.edit.selectedPathOptions)), t2.remove && (t2.remove = L.extend({}, this.options.remove, t2.remove)), t2.poly && (t2.poly = L.extend({}, this.options.poly, t2.poly)), this._toolbarClass = "leaflet-draw-edit", L.Toolbar.prototype.initialize.call(this, t2), this._selectedFeatureCount = 0;
    }, getModeHandlers: function(t2) {
      var e2 = this.options.featureGroup;
      return [{ enabled: this.options.edit, handler: new L.EditToolbar.Edit(t2, { featureGroup: e2, selectedPathOptions: this.options.edit.selectedPathOptions, poly: this.options.poly }), title: L.drawLocal.edit.toolbar.buttons.edit }, { enabled: this.options.remove, handler: new L.EditToolbar.Delete(t2, { featureGroup: e2 }), title: L.drawLocal.edit.toolbar.buttons.remove }];
    }, getActions: function(t2) {
      var e2 = [{ title: L.drawLocal.edit.toolbar.actions.save.title, text: L.drawLocal.edit.toolbar.actions.save.text, callback: this._save, context: this }, { title: L.drawLocal.edit.toolbar.actions.cancel.title, text: L.drawLocal.edit.toolbar.actions.cancel.text, callback: this.disable, context: this }];
      return t2.removeAllLayers && e2.push({ title: L.drawLocal.edit.toolbar.actions.clearAll.title, text: L.drawLocal.edit.toolbar.actions.clearAll.text, callback: this._clearAllLayers, context: this }), e2;
    }, addToolbar: function(t2) {
      var e2 = L.Toolbar.prototype.addToolbar.call(this, t2);
      return this._checkDisabled(), this.options.featureGroup.on("layeradd layerremove", this._checkDisabled, this), e2;
    }, removeToolbar: function() {
      this.options.featureGroup.off("layeradd layerremove", this._checkDisabled, this), L.Toolbar.prototype.removeToolbar.call(this);
    }, disable: function() {
      this.enabled() && (this._activeMode.handler.revertLayers(), L.Toolbar.prototype.disable.call(this));
    }, _save: function() {
      this._activeMode.handler.save(), this._activeMode && this._activeMode.handler.disable();
    }, _clearAllLayers: function() {
      this._activeMode.handler.removeAllLayers(), this._activeMode && this._activeMode.handler.disable();
    }, _checkDisabled: function() {
      var t2, e2 = this.options.featureGroup, i2 = 0 !== e2.getLayers().length;
      this.options.edit && (t2 = this._modes[L.EditToolbar.Edit.TYPE].button, i2 ? L.DomUtil.removeClass(t2, "leaflet-disabled") : L.DomUtil.addClass(t2, "leaflet-disabled"), t2.setAttribute("title", i2 ? L.drawLocal.edit.toolbar.buttons.edit : L.drawLocal.edit.toolbar.buttons.editDisabled)), this.options.remove && (t2 = this._modes[L.EditToolbar.Delete.TYPE].button, i2 ? L.DomUtil.removeClass(t2, "leaflet-disabled") : L.DomUtil.addClass(t2, "leaflet-disabled"), t2.setAttribute("title", i2 ? L.drawLocal.edit.toolbar.buttons.remove : L.drawLocal.edit.toolbar.buttons.removeDisabled));
    } }), L.EditToolbar.Edit = L.Handler.extend({ statics: { TYPE: "edit" }, initialize: function(t2, e2) {
      if (L.Handler.prototype.initialize.call(this, t2), L.setOptions(this, e2), this._featureGroup = e2.featureGroup, !(this._featureGroup instanceof L.FeatureGroup)) throw new Error("options.featureGroup must be a L.FeatureGroup");
      this._uneditedLayerProps = {}, this.type = L.EditToolbar.Edit.TYPE;
      var i2 = L.version.split(".");
      1 === parseInt(i2[0], 10) && parseInt(i2[1], 10) >= 2 ? L.EditToolbar.Edit.include(L.Evented.prototype) : L.EditToolbar.Edit.include(L.Mixin.Events);
    }, enable: function() {
      !this._enabled && this._hasAvailableLayers() && (this.fire("enabled", { handler: this.type }), this._map.fire(L.Draw.Event.EDITSTART, { handler: this.type }), L.Handler.prototype.enable.call(this), this._featureGroup.on("layeradd", this._enableLayerEdit, this).on("layerremove", this._disableLayerEdit, this));
    }, disable: function() {
      this._enabled && (this._featureGroup.off("layeradd", this._enableLayerEdit, this).off("layerremove", this._disableLayerEdit, this), L.Handler.prototype.disable.call(this), this._map.fire(L.Draw.Event.EDITSTOP, { handler: this.type }), this.fire("disabled", { handler: this.type }));
    }, addHooks: function() {
      var t2 = this._map;
      t2 && (t2.getContainer().focus(), this._featureGroup.eachLayer(this._enableLayerEdit, this), this._tooltip = new L.Draw.Tooltip(this._map), this._tooltip.updateContent({ text: L.drawLocal.edit.handlers.edit.tooltip.text, subtext: L.drawLocal.edit.handlers.edit.tooltip.subtext }), t2._editTooltip = this._tooltip, this._updateTooltip(), this._map.on("mousemove", this._onMouseMove, this).on("touchmove", this._onMouseMove, this).on("MSPointerMove", this._onMouseMove, this).on(L.Draw.Event.EDITVERTEX, this._updateTooltip, this));
    }, removeHooks: function() {
      this._map && (this._featureGroup.eachLayer(this._disableLayerEdit, this), this._uneditedLayerProps = {}, this._tooltip.dispose(), this._tooltip = null, this._map.off("mousemove", this._onMouseMove, this).off("touchmove", this._onMouseMove, this).off("MSPointerMove", this._onMouseMove, this).off(L.Draw.Event.EDITVERTEX, this._updateTooltip, this));
    }, revertLayers: function() {
      this._featureGroup.eachLayer(function(t2) {
        this._revertLayer(t2);
      }, this);
    }, save: function() {
      var t2 = new L.LayerGroup();
      this._featureGroup.eachLayer(function(e2) {
        e2.edited && (t2.addLayer(e2), e2.edited = false);
      }), this._map.fire(L.Draw.Event.EDITED, { layers: t2 });
    }, _backupLayer: function(t2) {
      var e2 = L.Util.stamp(t2);
      this._uneditedLayerProps[e2] || (t2 instanceof L.Polyline || t2 instanceof L.Polygon || t2 instanceof L.Rectangle ? this._uneditedLayerProps[e2] = { latlngs: L.LatLngUtil.cloneLatLngs(t2.getLatLngs()) } : t2 instanceof L.Circle ? this._uneditedLayerProps[e2] = { latlng: L.LatLngUtil.cloneLatLng(t2.getLatLng()), radius: t2.getRadius() } : (t2 instanceof L.Marker || t2 instanceof L.CircleMarker) && (this._uneditedLayerProps[e2] = { latlng: L.LatLngUtil.cloneLatLng(t2.getLatLng()) }));
    }, _getTooltipText: function() {
      return { text: L.drawLocal.edit.handlers.edit.tooltip.text, subtext: L.drawLocal.edit.handlers.edit.tooltip.subtext };
    }, _updateTooltip: function() {
      this._tooltip.updateContent(this._getTooltipText());
    }, _revertLayer: function(t2) {
      var e2 = L.Util.stamp(t2);
      t2.edited = false, this._uneditedLayerProps.hasOwnProperty(e2) && (t2 instanceof L.Polyline || t2 instanceof L.Polygon || t2 instanceof L.Rectangle ? t2.setLatLngs(this._uneditedLayerProps[e2].latlngs) : t2 instanceof L.Circle ? (t2.setLatLng(this._uneditedLayerProps[e2].latlng), t2.setRadius(this._uneditedLayerProps[e2].radius)) : (t2 instanceof L.Marker || t2 instanceof L.CircleMarker) && t2.setLatLng(this._uneditedLayerProps[e2].latlng), t2.fire("revert-edited", { layer: t2 }));
    }, _enableLayerEdit: function(t2) {
      var e2, i2, o2 = t2.layer || t2.target || t2;
      this._backupLayer(o2), this.options.poly && (i2 = L.Util.extend({}, this.options.poly), o2.options.poly = i2), this.options.selectedPathOptions && (e2 = L.Util.extend({}, this.options.selectedPathOptions), e2.maintainColor && (e2.color = o2.options.color, e2.fillColor = o2.options.fillColor), o2.options.original = L.extend({}, o2.options), o2.options.editing = e2), o2 instanceof L.Marker ? (o2.editing && o2.editing.enable(), o2.dragging.enable(), o2.on("dragend", this._onMarkerDragEnd).on("touchmove", this._onTouchMove, this).on("MSPointerMove", this._onTouchMove, this).on("touchend", this._onMarkerDragEnd, this).on("MSPointerUp", this._onMarkerDragEnd, this)) : o2.editing.enable();
    }, _disableLayerEdit: function(t2) {
      var e2 = t2.layer || t2.target || t2;
      e2.edited = false, e2.editing && e2.editing.disable(), delete e2.options.editing, delete e2.options.original, this._selectedPathOptions && (e2 instanceof L.Marker ? this._toggleMarkerHighlight(e2) : (e2.setStyle(e2.options.previousOptions), delete e2.options.previousOptions)), e2 instanceof L.Marker ? (e2.dragging.disable(), e2.off("dragend", this._onMarkerDragEnd, this).off("touchmove", this._onTouchMove, this).off("MSPointerMove", this._onTouchMove, this).off("touchend", this._onMarkerDragEnd, this).off("MSPointerUp", this._onMarkerDragEnd, this)) : e2.editing.disable();
    }, _onMouseMove: function(t2) {
      this._tooltip.updatePosition(t2.latlng);
    }, _onMarkerDragEnd: function(t2) {
      var e2 = t2.target;
      e2.edited = true, this._map.fire(L.Draw.Event.EDITMOVE, { layer: e2 });
    }, _onTouchMove: function(t2) {
      var e2 = t2.originalEvent.changedTouches[0], i2 = this._map.mouseEventToLayerPoint(e2), o2 = this._map.layerPointToLatLng(i2);
      t2.target.setLatLng(o2);
    }, _hasAvailableLayers: function() {
      return 0 !== this._featureGroup.getLayers().length;
    } }), L.EditToolbar.Delete = L.Handler.extend({ statics: { TYPE: "remove" }, initialize: function(t2, e2) {
      if (L.Handler.prototype.initialize.call(this, t2), L.Util.setOptions(this, e2), this._deletableLayers = this.options.featureGroup, !(this._deletableLayers instanceof L.FeatureGroup)) throw new Error("options.featureGroup must be a L.FeatureGroup");
      this.type = L.EditToolbar.Delete.TYPE;
      var i2 = L.version.split(".");
      1 === parseInt(i2[0], 10) && parseInt(i2[1], 10) >= 2 ? L.EditToolbar.Delete.include(L.Evented.prototype) : L.EditToolbar.Delete.include(L.Mixin.Events);
    }, enable: function() {
      !this._enabled && this._hasAvailableLayers() && (this.fire("enabled", { handler: this.type }), this._map.fire(L.Draw.Event.DELETESTART, { handler: this.type }), L.Handler.prototype.enable.call(this), this._deletableLayers.on("layeradd", this._enableLayerDelete, this).on("layerremove", this._disableLayerDelete, this));
    }, disable: function() {
      this._enabled && (this._deletableLayers.off("layeradd", this._enableLayerDelete, this).off("layerremove", this._disableLayerDelete, this), L.Handler.prototype.disable.call(this), this._map.fire(L.Draw.Event.DELETESTOP, { handler: this.type }), this.fire("disabled", { handler: this.type }));
    }, addHooks: function() {
      var t2 = this._map;
      t2 && (t2.getContainer().focus(), this._deletableLayers.eachLayer(this._enableLayerDelete, this), this._deletedLayers = new L.LayerGroup(), this._tooltip = new L.Draw.Tooltip(this._map), this._tooltip.updateContent({ text: L.drawLocal.edit.handlers.remove.tooltip.text }), this._map.on("mousemove", this._onMouseMove, this));
    }, removeHooks: function() {
      this._map && (this._deletableLayers.eachLayer(this._disableLayerDelete, this), this._deletedLayers = null, this._tooltip.dispose(), this._tooltip = null, this._map.off("mousemove", this._onMouseMove, this));
    }, revertLayers: function() {
      this._deletedLayers.eachLayer(function(t2) {
        this._deletableLayers.addLayer(t2), t2.fire("revert-deleted", { layer: t2 });
      }, this);
    }, save: function() {
      this._map.fire(L.Draw.Event.DELETED, { layers: this._deletedLayers });
    }, removeAllLayers: function() {
      this._deletableLayers.eachLayer(function(t2) {
        this._removeLayer({ layer: t2 });
      }, this), this.save();
    }, _enableLayerDelete: function(t2) {
      (t2.layer || t2.target || t2).on("click", this._removeLayer, this);
    }, _disableLayerDelete: function(t2) {
      var e2 = t2.layer || t2.target || t2;
      e2.off("click", this._removeLayer, this), this._deletedLayers.removeLayer(e2);
    }, _removeLayer: function(t2) {
      var e2 = t2.layer || t2.target || t2;
      this._deletableLayers.removeLayer(e2), this._deletedLayers.addLayer(e2), e2.fire("deleted");
    }, _onMouseMove: function(t2) {
      this._tooltip.updatePosition(t2.latlng);
    }, _hasAvailableLayers: function() {
      return 0 !== this._deletableLayers.getLayers().length;
    } });
  }(window, document);

  // components/agrolattice_boundary_editor/src.js
  var map = null;
  var editable = null;
  var drawControl = null;
  function setStatus(message, tone = "normal") {
    const box = document.getElementById("status");
    box.textContent = message;
    box.dataset.tone = tone;
  }
  var OfflineGrid = import_leaflet.default.GridLayer.extend({
    createTile(coords) {
      const tile = document.createElement("canvas");
      tile.width = 256;
      tile.height = 256;
      const ctx = tile.getContext("2d");
      ctx.fillStyle = "#eef2f3";
      ctx.fillRect(0, 0, 256, 256);
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 1;
      for (let value = 0; value <= 256; value += 32) {
        ctx.beginPath();
        ctx.moveTo(value, 0);
        ctx.lineTo(value, 256);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, value);
        ctx.lineTo(256, value);
        ctx.stroke();
      }
      ctx.fillStyle = "#64748b";
      ctx.font = "600 12px system-ui, sans-serif";
      ctx.fillText(`offline grid \xB7 z${coords.z}`, 12, 24);
      return tile;
    }
  });
  function geometryOnly(feature) {
    if (!feature) return null;
    if (feature.type === "Feature") return feature.geometry;
    if (feature.type === "FeatureCollection") {
      const polygons = (feature.features || []).map((item) => item.geometry).filter(Boolean);
      if (polygons.length === 1) return polygons[0];
      return { type: "GeometryCollection", geometries: polygons };
    }
    return feature;
  }
  function emitGeometry(action = "updated") {
    const layers = editable.getLayers();
    if (!layers.length) {
      Streamlit.setComponentValue({ geometry: null, action: "deleted" });
      setStatus("No editable boundary. Draw a polygon or rectangle.", "warning");
      return;
    }
    const collection = editable.toGeoJSON();
    let geometry = null;
    if (collection.features.length === 1) {
      geometry = collection.features[0].geometry;
    } else {
      geometry = {
        type: "MultiPolygon",
        coordinates: collection.features.map((item) => item.geometry).filter((item) => item && item.type === "Polygon").map((item) => item.coordinates)
      };
    }
    Streamlit.setComponentValue({ geometry, action });
    setStatus("Boundary captured locally. Save it in the form below.", "success");
  }
  function addEditableGeometry(geometry) {
    if (!geometry) return;
    try {
      const layer = import_leaflet.default.geoJSON(geometry, {
        style: { color: "#dc2626", weight: 4, fillColor: "#fb7185", fillOpacity: 0.18 }
      });
      layer.eachLayer((child) => editable.addLayer(child));
    } catch (error) {
      setStatus(`Saved boundary could not be loaded: ${error.message}`, "warning");
    }
  }
  function addReferenceGeometry(item, index, bounds) {
    if (!item || !item.geometry) return;
    const colour = item.color || "#059669";
    const layer = import_leaflet.default.geoJSON(item.geometry, {
      style: {
        color: colour,
        weight: Number(item.weight || 4),
        dashArray: item.dash || "9 6",
        fillColor: colour,
        fillOpacity: Number(item.fill_opacity ?? 0.04)
      }
    }).bindTooltip(item.label || `Reference boundary ${index + 1}`);
    layer.addTo(map);
    if (layer.getBounds && layer.getBounds().isValid()) bounds.push(layer.getBounds());
  }
  function render(event) {
    const args = event.detail.args || {};
    const height = Math.max(360, Number(args.height || 520));
    document.documentElement.style.setProperty("--map-height", `${height}px`);
    Streamlit.setFrameHeight(height + 8);
    if (map) {
      map.off();
      map.remove();
      map = null;
    }
    document.getElementById("map").innerHTML = "";
    const center = Array.isArray(args.center) && args.center.length === 2 ? args.center : [19.45, -98.9];
    map = import_leaflet.default.map("map", { center, zoom: Number(args.zoom || 15), zoomControl: true, preferCanvas: true });
    const offline = new OfflineGrid({ minZoom: 2, maxZoom: 22, attribution: "AGROLATTICE offline grid" });
    const roads = import_leaflet.default.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 20,
      attribution: "\xA9 OpenStreetMap contributors",
      crossOrigin: true
    });
    const satellite = import_leaflet.default.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 20,
      attribution: "Esri, Maxar, Earthstar Geographics",
      crossOrigin: true
    });
    const bases = { "Satellite imagery": satellite, "Roads & places": roads, "Offline grid": offline };
    let active = args.satellite_default === false ? roads : satellite;
    active.addTo(map);
    import_leaflet.default.control.layers(bases, {}, { position: "topright", collapsed: false }).addTo(map);
    import_leaflet.default.control.scale({ metric: true, imperial: false }).addTo(map);
    let tileErrors = 0;
    function handleTileError() {
      tileErrors += 1;
      if (tileErrors >= 4 && !map.hasLayer(offline)) {
        map.removeLayer(active);
        active = offline;
        offline.addTo(map);
        setStatus("Online tiles are unavailable; the local editor switched to its offline grid.", "warning");
      }
    }
    roads.on("tileerror", handleTileError);
    satellite.on("tileerror", handleTileError);
    editable = new import_leaflet.default.FeatureGroup();
    editable.addTo(map);
    addEditableGeometry(geometryOnly(args.initial_geometry));
    const allBounds = [];
    if (editable.getLayers().length) {
      const editableBounds = editable.getBounds();
      if (editableBounds.isValid()) allBounds.push(editableBounds);
    }
    (args.reference_geometries || []).forEach((item, index) => addReferenceGeometry(item, index, allBounds));
    if (args.drawing_enabled !== false) {
      drawControl = new import_leaflet.default.Control.Draw({
        position: "topleft",
        draw: {
          polygon: { allowIntersection: false, showArea: true, metric: true, shapeOptions: { color: "#dc2626", weight: 4 } },
          rectangle: { showArea: true, metric: true, shapeOptions: { color: "#dc2626", weight: 4 } },
          polyline: false,
          circle: false,
          circlemarker: false,
          marker: false
        },
        edit: { featureGroup: editable, edit: true, remove: true }
      });
      map.addControl(drawControl);
      map.on(import_leaflet.default.Draw.Event.CREATED, (drawEvent) => {
        editable.clearLayers();
        editable.addLayer(drawEvent.layer);
        emitGeometry("created");
      });
      map.on(import_leaflet.default.Draw.Event.EDITED, () => emitGeometry("edited"));
      map.on(import_leaflet.default.Draw.Event.DELETED, () => emitGeometry("deleted"));
    }
    if (allBounds.length) {
      const combined = allBounds.reduce((result, item) => result.extend(item), import_leaflet.default.latLngBounds([]));
      if (combined.isValid()) map.fitBounds(combined, { padding: [28, 28], maxZoom: 19 });
    }
    setTimeout(() => map.invalidateSize(), 50);
    setStatus(editable.getLayers().length ? "Saved boundary loaded. Use edit or delete to change it." : "Draw a polygon or rectangle. The editor is loaded from this installation.");
  }
  Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, render);
  Streamlit.setComponentReady();
  Streamlit.setFrameHeight(528);
})();
/*! Bundled license information:

react-is/cjs/react-is.development.js:
  (** @license React v16.13.1
   * react-is.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)

object-assign/index.js:
  (*
  object-assign
  (c) Sindre Sorhus
  @license MIT
  *)

react/cjs/react.development.js:
  (** @license React v16.14.0
   * react.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)

leaflet/dist/leaflet-src.js:
  (* @preserve
   * Leaflet 1.9.4, a JS library for interactive maps. https://leafletjs.com
   * (c) 2010-2023 Vladimir Agafonkin, (c) 2010-2011 CloudMade
   *)
*/
